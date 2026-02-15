from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .models import ChatRequest, ChatResponse
from .service import ChatService

settings = get_settings()
service = ChatService(settings)

app = FastAPI(title="Nusus AI", version="0.1.0")

if settings.public_launch_reminder:
    print(
        "[Nusus AI reminder] Public launch checklist is pending: auth boundaries, abuse controls, privacy/logging policy, and key management."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8010", "http://127.0.0.1:8010", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_local_client(host: str | None) -> bool:
    if not host:
        return False
    if host in {"127.0.0.1", "::1", "localhost"}:
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "db_path": str(settings.db_path),
        "server_key_enabled": "yes" if bool(settings.openai_api_key) else "no",
        "local_only_mode": "yes" if settings.local_only else "no",
        "public_launch_reminder": "yes" if settings.public_launch_reminder else "no",
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    request: Request,
    x_openai_api_key: str | None = Header(default=None),
) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    if settings.local_only and not _is_local_client(request.client.host if request.client else None):
        raise HTTPException(status_code=403, detail="Local-only mode is enabled.")

    try:
        return service.answer(
            question=question,
            top_k=payload.top_k,
            max_opinions=payload.max_opinions,
            user_openai_api_key=x_openai_api_key,
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
