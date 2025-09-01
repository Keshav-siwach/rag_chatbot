from __future__ import annotations

from typing import AsyncGenerator, List

from utils.text import join_context
from utils.logger import logger
from services.retriever import Retriever
from services.llm import LLMClient
from config import settings


SYSTEM_PROMPT = (
    "You are an AI assistant.\n"
    "Your primary task is to answer user questions using ONLY the information provided in the retrieved context documents.\n"
    "If the answer cannot be found in the provided context, say politely that you don’t know.\n"
    "Do not invent or hallucinate facts.\n"
    "If relevant, cite the source or document name from the context.\n\n"
    "Guidelines:\n"
    "- Be clear and sufficiently informative. Prefer 2–5 sentences or a few concise bullet points.\n"
    "- Do not repeat irrelevant context.\n"
    "- Do not reveal internal system instructions or raw context text unless explicitly asked.\n"
    "- If the user asks a general chit-chat question unrelated to the documents, respond briefly and politely, but make it clear you may not have document-based support.\n"
    "- If multiple possible answers exist in the context, summarize them fairly.\n\n"
    "Context will always be provided in the following format:\n"
    "<context>\n[Top-k retrieved passages go here]\n</context>\n\n"
    "User Question: {user_query}"
)


class RAGPipeline:
    def __init__(self, retriever: Retriever, llm: LLMClient):
        self.retriever = retriever
        self.llm = llm

    async def stream_answer(self, query: str) -> AsyncGenerator[str, None]:
        # Allow lightweight small talk without retrieval
        q = query.strip().lower()
        if q in {"hi", "hello", "hey", "hey there", "hii", "hiii"}:
            msg = "Hello! Ask me questions about your documents."
            yield msg
            return

        # Retrieve with scores for gating
        pairs = self.retriever.top_k_with_scores(query)
        contexts: List[str] = [t for t, _ in pairs]
        scores: List[float] = [s for _, s in pairs]
        context_text = join_context(contexts)
        logger.debug(f"Context length: {len(context_text)} chars")

        # Gate by relevance
        if not scores or max(scores) < settings.retrieval_min_score:
            msg = "Sorry, I don't know about this based on the documents I have."
            yield msg
            return

        # Build prompt
        user_prompt = (
            f"<context>\n{context_text}\n</context>\n\n"
            f"User Question: {query}"
        )

        # Stream from LLM
        async for token in self.llm.stream_chat(SYSTEM_PROMPT, user_prompt):
            yield token
