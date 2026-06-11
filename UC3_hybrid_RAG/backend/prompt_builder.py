"""Strict context builder and citation helpers."""

from __future__ import annotations

from .schemas import Citation, HybridEvidence


REFUSAL = "Information not found in the source document."

SYSTEM_PROMPT = f"""
You are a retrieval-grounded NCERT Physics assistant.
Answer only from the provided context.
Do not use outside knowledge.
Do not infer facts that are not supported by the context.
If the answer is unavailable in the context, say exactly:
{REFUSAL}
Keep the answer concise and cite only the supplied source context.
""".strip()


def build_context(evidence: HybridEvidence, max_chars: int = 14000) -> str:
    sections: list[str] = []

    for index, item in enumerate(evidence.merged_chunks, start=1):
        meta = item.metadata
        sections.append(
            "\n".join(
                [
                    f"[Chunk {index}]",
                    f"Chapter: {meta.get('chapter', '')}",
                    f"Section: {meta.get('section', '')}",
                    f"Page: {meta.get('pages') or meta.get('page', '')}",
                    item.text,
                ]
            )
        )

    if evidence.graph_nodes:
        graph_lines = ["[Graph Evidence]"]
        for node in evidence.graph_nodes:
            graph_lines.append(
                " | ".join(
                    part
                    for part in [
                        f"{node.node_label}: {node.node_name}",
                        node.relationship,
                        f"{node.neighbor_label}: {node.neighbor_name}" if node.neighbor_name else "",
                        f"Page: {node.metadata.get('pages') or node.metadata.get('page', '')}",
                    ]
                    if part
                )
            )
        sections.append("\n".join(graph_lines))

    context = "\n\n---\n\n".join(sections)
    if len(context) > max_chars:
        return context[:max_chars] + "\n\n[Context truncated]"
    return context


def build_messages(question: str, evidence: HybridEvidence, max_context_chars: int) -> list[dict[str, str]]:
    context = build_context(evidence, max_context_chars)
    normalized_line = ""
    if evidence.retrieval_query and evidence.retrieval_query != question:
        normalized_line = f"\nNormalized retrieval query:\n{evidence.retrieval_query}\n"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Question:\n{question}\n{normalized_line}\nRetrieved context:\n{context}",
        },
    ]


def collect_citations(evidence: HybridEvidence, limit: int = 8) -> list[Citation]:
    seen: set[tuple[str, str, str, str]] = set()
    citations: list[Citation] = []

    for item in evidence.merged_chunks:
        meta = item.metadata
        citation = Citation(
            chapter=str(meta.get("chapter", "")),
            section=str(meta.get("section", "")),
            page=str(meta.get("pages") or meta.get("page", "")),
            source=str(meta.get("source", "")),
        )
        key = (citation.chapter, citation.section, citation.page, citation.source)
        if key not in seen:
            seen.add(key)
            citations.append(citation)
        if len(citations) >= limit:
            return citations

    for node in evidence.graph_nodes:
        meta = node.metadata
        citation = Citation(
            chapter=str(meta.get("chapter", "")),
            section=str(meta.get("section", "")),
            page=str(meta.get("pages") or meta.get("page", "")),
            source=str(meta.get("source", "")),
        )
        key = (citation.chapter, citation.section, citation.page, citation.source)
        if key not in seen and citation.page:
            seen.add(key)
            citations.append(citation)
        if len(citations) >= limit:
            break

    return citations


def format_sources(citations: list[Citation]) -> str:
    if not citations:
        return "Sources:\nNone"
    return "Sources:\n" + "\n\n".join(citation.to_text() for citation in citations)
