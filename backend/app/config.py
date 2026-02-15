from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    db_path: Path
    openai_api_key: str
    openai_model: str
    local_only: bool
    public_launch_reminder: bool
    max_retrieval_candidates: int
    default_top_k: int
    default_max_opinions: int


def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[2]
    db_path = Path(os.getenv("NUSUS_DB_PATH", "./data/corpus.sqlite"))
    if not db_path.is_absolute():
        db_path = (repo_root / db_path).resolve()

    return Settings(
        repo_root=repo_root,
        db_path=db_path,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        local_only=os.getenv("LOCAL_ONLY_MODE", "1") == "1",
        public_launch_reminder=os.getenv("PUBLIC_LAUNCH_REMINDER", "1") == "1",
        max_retrieval_candidates=max(5, int(os.getenv("MAX_RETRIEVAL_CANDIDATES", "30"))),
        default_top_k=max(3, int(os.getenv("DEFAULT_TOP_K", "12"))),
        default_max_opinions=max(2, int(os.getenv("DEFAULT_MAX_OPINIONS", "4"))),
    )
