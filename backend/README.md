# RAG Chatbot Backend

## Overview
This backend implements a simple, production-ready Retrieval-Augmented Generation (RAG) pipeline with:
- HuggingFace embeddings for document and query vectors
- FAISS (or NumPy fallback) vector store for retrieval
- OpenAI LLM for grounded, concise answer generation
- FastAPI WebSocket endpoint for streaming responses

## Components
- Embeddings: services/embeddings.py (Sentence-Transformers via EMBEDDING_MODEL)
- Vector store: db/vector_store.py (FAISS index with ids.txt mapping; NumPy fallback)
- Ingestion: scripts/ingest.py (reads data/docs, chunks text, embeds, writes index)
- Retriever: services/retriever.py (MMR diversification + metadata)
- RAG pipeline: services/rag.py (builds context with citations, gates low relevance)
- LLM: services/llm.py (OpenAI streaming with token/temperature controls)
- API: main.py (WebSocket /chat, /health)
- Utils: utils/text.py (sentence chunking with 1-sentence overlap), utils/logger.py

## Data & Index Paths
- Documents: backend/data/docs
- Index output: backend/data/index
  - faiss.index (optional if faiss installed)
  - docstore.jsonl (chunk texts + metadata)
  - embeddings.npy (NumPy fallback)
  - ids.txt (mapping for FAISS results → doc IDs)

## Environment Variables (.env)
- Embeddings
  - EMBEDDING_MODEL (default: sentence-transformers/all-MiniLM-L6-v2)
- Vector store
  - FAISS_INDEX_PATH (optional)
  - DOCSTORE_PATH (optional)
  - TOP_K (default 5)
  - RETRIEVAL_MIN_SCORE (default 0.2)
  - MMR_FETCH_FACTOR (default 4)
  - MMR_LAMBDA (default 0.5)
- LLM (OpenAI)
  - OPENAI_API_KEY (required)
  - OPENAI_MODEL (default gpt-4o-mini)
  - ANSWER_MAX_TOKENS (default 256)
  - LLM_TEMPERATURE (default 0.2)
- Context
  - CONTEXT_CHAR_LIMIT (default 6000)
- Server
  - HOST, PORT, CORS_ORIGINS, LOG_LEVEL

## Typical Flow
1) Ingest
- Place .txt/.pdf files in backend/data/docs
- Run: `python backend/scripts/ingest.py`
  - Splits text → chunks (utils/text.py)
  - Embeds chunks (services/embeddings.py)
  - Saves docstore.jsonl, embeddings.npy, ids.txt, and faiss.index (if available)

2) Serve
- Start API: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- Client connects to `ws://<host>:8000/chat`, sends `{"question": "..."}` or plain text
- Server streams tokens, then `__END__`

## Sequence (High Level)
```
Client --(question)--> RAGPipeline
RAGPipeline --(embed query)--> Embeddings
RAGPipeline --(search)--> VectorStore (FAISS/NumPy)
RAGPipeline --(MMR select)--> Retriever
RAGPipeline --(build context + prompt)--> LLM (OpenAI)
LLM --(stream tokens)--> Client
```

## Tuning Tips
- Retrieval: adjust TOP_K (5–8), RETRIEVAL_MIN_SCORE (~0.15–0.25), MMR_FETCH_FACTOR (3–5), MMR_LAMBDA (0.3–0.7)
- Answer length: ANSWER_MAX_TOKENS (200–300 typical), LLM_TEMPERATURE (0.1–0.3 for factual)
- Context size: CONTEXT_CHAR_LIMIT to prevent overlong prompts
- Chunking: utils/text.py uses sentence-based splitting with small overlap; change max_tokens in scripts/ingest.py if needed

## Health & Logs
- GET /health → { status: ok, vector_store_ready: true/false }
- Configure LOG_LEVEL (INFO/DEBUG) for verbosity

## Notes
- FAISS is optional; if unavailable, NumPy fallback will be used for retrieval.
- Ensure OPENAI_API_KEY is set for production. Without it, the server will fail to initialize LLM.
