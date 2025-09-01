from __future__ import annotations

import json
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from utils.logger import logger
from services.embeddings import EmbeddingClient
from db.vector_store import VectorStore
from services.retriever import Retriever
from services.llm import LLMClient
from services.rag import RAGPipeline

app = FastAPI(title="RAG Chatbot Backend")

# CORS for local dev
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services
_embedder = EmbeddingClient()
_store = VectorStore(dim=_embedder.dim or 384)
_store.load()
_retriever = Retriever(_embedder, _store)
_llm = LLMClient()
_rag = RAGPipeline(_retriever, _llm)


@app.get("/health")
async def health():
    return {"status": "ok", "vector_store_ready": _store.is_ready()}


@app.websocket("/chat")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket connected")
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
                question: Optional[str] = payload.get("question")
            except Exception:
                question = raw

            if not question:
                await ws.send_text("Error: empty question.")
                continue

            # Start streaming answer
            async for token in _rag.stream_answer(question):
                await ws.send_text(token)
            # Signal completion to client
            await ws.send_text("__END__")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await ws.send_text("__ERROR__")
        except Exception:
            pass
