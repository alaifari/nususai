from __future__ import annotations

from collections import defaultdict

from langdetect import DetectorFactory, LangDetectException, detect

from .config import Settings
from .llm import LLMClient
from .models import ChatResponse, Citation, Opinion
from .retrieval import Passage, CorpusRetriever, pick_diverse_passages

DetectorFactory.seed = 0


class ChatService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.retriever = CorpusRetriever(settings.db_path)
        self.llm = LLMClient(settings)

    def answer(self, question: str, top_k: int | None = None, max_opinions: int | None = None) -> ChatResponse:
        top_k = top_k or self.settings.default_top_k
        max_opinions = max_opinions or self.settings.default_max_opinions
        lang = self.detect_language(question)

        translated_query = None
        if lang != "ar":
            translated_query = self.llm.translate_to_arabic(question)

        search_query = translated_query or question
        raw_hits = self.retriever.search(search_query, limit=max(self.settings.max_retrieval_candidates, top_k))
        selected = pick_diverse_passages(raw_hits, max_items=top_k)

        if not selected:
            return ChatResponse(
                answer=self._no_results_answer(lang),
                language=lang,
                opinions=[],
                citations=[],
                notes=["No matching passages found in current local index."],
            )

        llm_payload = self.llm.build_answer(question, lang, selected, max_opinions=max_opinions)

        if llm_payload:
            return self._build_response_from_llm(lang, llm_payload, selected)

        return self._build_fallback_response(lang, selected, max_opinions)

    @staticmethod
    def detect_language(text: str) -> str:
        try:
            return detect(text)
        except LangDetectException:
            return "und"

    def _build_response_from_llm(self, lang: str, llm_payload: dict, selected: list[Passage]) -> ChatResponse:
        citation_map = {p.id: self._to_citation(p) for p in selected}

        opinions: list[Opinion] = []
        for op in llm_payload.get("opinions", []):
            if not isinstance(op, dict):
                continue
            citation_ids = [cid for cid in op.get("citation_ids", []) if cid in citation_map]
            if not citation_ids:
                continue
            opinions.append(
                Opinion(
                    title=str(op.get("title", "Opinion")).strip() or "Opinion",
                    summary=str(op.get("summary", "")).strip(),
                    citation_ids=citation_ids,
                )
            )

        if not opinions:
            return self._build_fallback_response(lang, selected, self.settings.default_max_opinions)

        used_ids = []
        for opinion in opinions:
            for cid in opinion.citation_ids:
                if cid not in used_ids:
                    used_ids.append(cid)

        answer = str(llm_payload.get("answer", "")).strip()
        if not answer:
            answer = self._fallback_summary(lang, selected)

        return ChatResponse(
            answer=answer,
            language=lang,
            opinions=opinions,
            citations=[citation_map[cid] for cid in used_ids],
            notes=[] if self.llm.enabled else ["OPENAI_API_KEY not set; using extractive fallback mode."],
        )

    def _build_fallback_response(self, lang: str, selected: list[Passage], max_opinions: int) -> ChatResponse:
        grouped: dict[str, list[Passage]] = defaultdict(list)
        for p in selected:
            key = f"{p.book_title_ar} - {p.author_ar}"
            grouped[key].append(p)

        opinions: list[Opinion] = []
        used_ids: list[str] = []

        for key, items in grouped.items():
            if len(opinions) >= max_opinions:
                break

            primary = items[0]
            quote = primary.snippet_ar.strip()
            summary = self._fallback_opinion_text(lang, quote)
            citation_ids = [p.id for p in items[:2]]

            opinions.append(
                Opinion(title=key, summary=summary, citation_ids=citation_ids)
            )
            for cid in citation_ids:
                if cid not in used_ids:
                    used_ids.append(cid)

        citation_map = {p.id: self._to_citation(p) for p in selected}

        return ChatResponse(
            answer=self._fallback_summary(lang, selected),
            language=lang,
            opinions=opinions,
            citations=[citation_map[cid] for cid in used_ids if cid in citation_map],
            notes=["OPENAI_API_KEY not set; using extractive fallback mode."],
        )

    @staticmethod
    def _to_citation(p: Passage) -> Citation:
        return Citation(
            id=p.id,
            book_title_ar=p.book_title_ar,
            author_ar=p.author_ar,
            source_ref_ar=p.source_ref_ar,
            volume=p.volume,
            page=p.page,
            snippet_ar=p.snippet_ar,
            score=p.score,
        )

    @staticmethod
    def _fallback_summary(lang: str, selected: list[Passage]) -> str:
        if lang == "ar":
            return "فيما يلي خلاصة مبنية على نصوص من الشاملة مع عرض آراء متعددة وتوثيق كل رأي بمصدره."
        return "Below is a source-grounded summary from primary texts, with multiple viewpoints and explicit citations."

    @staticmethod
    def _fallback_opinion_text(lang: str, quote: str) -> str:
        trimmed = " ".join(quote.split())[:260]
        if lang == "ar":
            return f"يركز هذا المصدر على: {trimmed}"
        return f"This source emphasizes: {trimmed}"

    @staticmethod
    def _no_results_answer(lang: str) -> str:
        if lang == "ar":
            return "لم أجد نتائج كافية في الفهرس الحالي. يرجى تجربة صياغة أخرى أو توسيع بيانات الشاملة المستوردة."
        return "No sufficient matches were found in the current local index. Try rephrasing or importing more source data."
