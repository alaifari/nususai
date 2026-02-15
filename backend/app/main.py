from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .models import ChatRequest, ChatResponse
from .service import ChatService

settings = get_settings()
service = ChatService(settings)

app = FastAPI(title="Nusus AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "db_path": str(settings.db_path),
        "llm_enabled": "yes" if bool(settings.openai_api_key) else "no",
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    try:
        return service.answer(
            question=question,
            top_k=payload.top_k,
            max_opinions=payload.max_opinions,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {exc}") from exc


frontend_root = Path(__file__).resolve().parents[2]
index_file = frontend_root / "index.html"


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(index_file)


app.mount("/", StaticFiles(directory=frontend_root, html=True), name="frontend")
