from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import Settings
from .retrieval import Passage


class LLMClient:
    def __init__(self, settings: Settings):
        self.enabled = bool(settings.openai_api_key)
        self.model = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled else None

    def translate_to_arabic(self, text: str) -> str | None:
        if not self.enabled:
            return None

        messages = [
            {
                "role": "system",
                "content": "You are a precise translator. Return only Arabic translation with no explanation.",
            },
            {"role": "user", "content": text},
        ]
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0)
            translated = (response.choices[0].message.content or "").strip()
            return translated or None
        except Exception:
            return None

    def build_answer(
        self,
        question: str,
        question_language: str,
        passages: list[Passage],
        max_opinions: int,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        context_lines = []
        for p in passages:
            context_lines.append(
                f"[id={p.id}] الكتاب: {p.book_title_ar} | المؤلف: {p.author_ar} | المرجع: {p.source_ref_ar} | النص: {p.snippet_ar}"
            )
        context = "\n".join(context_lines)

        schema_hint = {
            "answer": "string",
            "opinions": [
                {
                    "title": "string",
                    "summary": "string",
                    "citation_ids": ["id1", "id2"],
                }
            ],
        }

        system_prompt = (
            "You are Nusus AI. Build answers strictly from provided sources from the local corpus. "
            "Return different scholarly opinions where sources differ. "
            "Answer must be in the same language as the user question. "
            "Citations themselves remain in Arabic metadata and are handled by backend. "
            "Never invent citations or facts outside provided context. "
            "Return valid JSON only."
        )

        user_prompt = (
            f"Question language: {question_language}\n"
            f"Question: {question}\n"
            f"Max opinions: {max_opinions}\n"
            f"JSON schema shape: {json.dumps(schema_hint, ensure_ascii=False)}\n"
            "Use only these sources:\n"
            f"{context}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw = (response.choices[0].message.content or "").strip()
            if not raw:
                return None

            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None
