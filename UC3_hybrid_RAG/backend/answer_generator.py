"""Grounded LLM answer generation with configurable providers."""

from __future__ import annotations

import json
import re
import time

import requests

from .config import Settings, get_settings
from .logging_utils import get_logger
from .prompt_builder import REFUSAL, build_context, build_messages, collect_citations, format_sources
from .schemas import AnswerResult, HybridEvidence


LOGGER = get_logger(__name__)


class AnswerGenerator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def answer(self, question: str, evidence: HybridEvidence) -> AnswerResult:
        started = time.perf_counter()
        context = build_context(evidence, self.settings.max_context_chars)
        messages = build_messages(question, evidence, self.settings.max_context_chars)
        debug = self._build_debug(messages, context, evidence)

        if not evidence.has_context():
            answer = f"{REFUSAL}\n\n{format_sources([])}"
            return AnswerResult(answer=answer, citations=[], evidence=evidence, latency_ms=0.0, debug=debug)

        provider = self.settings.llm_provider
        LOGGER.info("Generating grounded answer with provider=%s", provider)

        if provider == "groq":
            raw = self._groq(messages)
        elif provider == "openai":
            raw = self._openai(messages)
        elif provider == "ollama":
            raw = self._ollama(messages)
        elif provider == "mistral":
            raw = self._mistral(messages)
        elif provider in {"llama", "llama.cpp", "llamacpp"}:
            raw = self._llama_cpp(messages)
        elif provider in {"extractive", "local"}:
            raw = self._extractive(question, evidence)
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

        citations = [] if REFUSAL in raw else collect_citations(evidence)
        body = self._strip_sources(raw)
        if not body:
            body = REFUSAL
            citations = []

        answer = f"{body}\n\n{format_sources(citations)}"
        latency_ms = (time.perf_counter() - started) * 1000
        LOGGER.info("LLM response generated in %.2f ms", latency_ms)
        return AnswerResult(
            answer=answer,
            citations=citations,
            evidence=evidence,
            latency_ms=latency_ms,
            debug=debug,
        )

    def _build_debug(
        self,
        messages: list[dict[str, str]],
        context: str,
        evidence: HybridEvidence,
    ) -> dict[str, object]:
        semantic_count = len(evidence.semantic_chunks)
        keyword_count = len(evidence.keyword_chunks)
        retrieved_chunk_count = semantic_count + keyword_count
        final_chunk_count = len(evidence.merged_chunks)
        provider = self.settings.llm_provider
        model = {
            "groq": self.settings.groq_model,
            "openai": self.settings.openai_model,
            "ollama": self.settings.ollama_model,
            "mistral": self.settings.mistral_model,
            "llama": self.settings.llama_model,
            "llama.cpp": self.settings.llama_model,
            "llamacpp": self.settings.llama_model,
            "extractive": "extractive",
            "local": "extractive",
        }.get(provider, "")

        return {
            "llm_provider": provider,
            "llm_model": model,
            "original_query": evidence.original_query,
            "retrieval_query": evidence.retrieval_query,
            "score_thresholds_enabled": False,
            "score_threshold_note": "No retrieval score thresholds are applied; top_k still limits each retriever.",
            "semantic_retrieved_count": semantic_count,
            "keyword_retrieved_count": keyword_count,
            "graph_retrieved_count": len(evidence.graph_nodes),
            "retrieved_chunk_count": retrieved_chunk_count,
            "final_chunk_count": final_chunk_count,
            "chunks_survived_filtering_count": final_chunk_count,
            "deduplicated_chunk_count": max(0, retrieved_chunk_count - final_chunk_count),
            "context_char_count": len(context),
            "max_context_chars": self.settings.max_context_chars,
            "context_truncated": context.endswith("[Context truncated]"),
            "exact_context_sent_to_llm": context,
            "exact_prompt_sent_to_llm": json.dumps(messages, indent=2, ensure_ascii=False),
            "llm_messages": messages,
            "final_chunks_passed_to_llm": [item.to_dict() for item in evidence.merged_chunks],
        }

    def _groq(self, messages: list[dict[str, str]]) -> str:
        if not self.settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY must be set for LLM_PROVIDER=groq")

        response = requests.post(
            f"{self.settings.groq_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.groq_model,
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"] or ""

    def _openai(self, messages: list[dict[str, str]]) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for LLM_PROVIDER=openai")
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(model=self.settings.openai_model, messages=messages)
        return response.choices[0].message.content or ""

    def _ollama(self, messages: list[dict[str, str]]) -> str:
        response = requests.post(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/chat",
            json={"model": self.settings.ollama_model, "messages": messages, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    def _mistral(self, messages: list[dict[str, str]]) -> str:
        if not self.settings.mistral_api_key:
            raise RuntimeError("MISTRAL_API_KEY must be set for LLM_PROVIDER=mistral")
        from mistralai import Mistral

        client = Mistral(api_key=self.settings.mistral_api_key)
        response = client.chat.complete(model=self.settings.mistral_model, messages=messages)
        return response.choices[0].message.content or ""

    def _llama_cpp(self, messages: list[dict[str, str]]) -> str:
        response = requests.post(
            f"{self.settings.llama_base_url.rstrip('/')}/v1/chat/completions",
            json={"model": self.settings.llama_model, "messages": messages},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _extractive(question: str, evidence: HybridEvidence) -> str:
        terms = {token.lower() for token in re.findall(r"[A-Za-z0-9]{3,}", question)}
        sentences: list[str] = []
        for item in evidence.merged_chunks[:5]:
            for sentence in re.split(r"(?<=[.!?])\s+", item.text.replace("\n", " ")):
                if any(term in sentence.lower() for term in terms):
                    sentences.append(sentence.strip())
                if len(sentences) >= 4:
                    break
            if len(sentences) >= 4:
                break
        if not sentences:
            return REFUSAL
        return " ".join(sentences)

    @staticmethod
    def _strip_sources(text: str) -> str:
        return re.split(r"\n\s*Sources\s*:", text.strip(), flags=re.IGNORECASE)[0].strip()
