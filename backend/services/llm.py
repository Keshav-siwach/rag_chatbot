from __future__ import annotations

import asyncio
from typing import AsyncGenerator, List

from config import settings
from utils.logger import logger


class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self._openai_async = None
        if self.provider == "openai" and settings.openai_api_key:
            try:  # pragma: no cover - optional
                from openai import AsyncOpenAI  # type: ignore
                self._openai_async = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info(f"Using OpenAI LLM: {settings.openai_model}")
            except Exception as e:
                logger.error(f"Failed to init OpenAI client: {e}")

    async def stream_chat(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        if self._openai_async is not None:
            try:  # pragma: no cover - optional
                stream = await self._openai_async.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    stream=True,
                )
                async for event in stream:
                    for choice in event.choices:
                        delta = getattr(choice, "delta", None) or getattr(choice, "message", None)
                        content = getattr(delta, "content", None) if delta else None
                        if content:
                            yield content
            except Exception as e:
                logger.error(f"OpenAI streaming failed, falling back to dummy: {e}")
                async for token in self._dummy_stream(system_prompt, user_prompt):
                    yield token
            return
        # HuggingFace or dummy fallback: synthesize a response deterministically
        async for token in self._dummy_stream(system_prompt, user_prompt):
            yield token

    async def _dummy_stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        text = (
            "Here is a helpful answer based on the provided context. "
            "(Note: Running in local dev mode without an external LLM API key.) "
        )
        combined = text + user_prompt
        for i in range(0, len(combined), 8):
            await asyncio.sleep(0.02)
            yield combined[i : i + 8]
