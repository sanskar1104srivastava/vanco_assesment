"""Streamlit frontend for the Hybrid RAG assessment app."""

from __future__ import annotations

import os
import re
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


def _render_chunk(item: dict[str, Any], key_prefix: str) -> None:
    meta = item.get("metadata", {})
    st.markdown(
        f"**Score:** {item.get('score', 0):.3f}  "
        f"**Chapter:** {meta.get('chapter', '')}  "
        f"**Section:** {meta.get('section', '')}  "
        f"**Page:** {meta.get('pages') or meta.get('page', '')}"
    )
    st.text_area(
        "Chunk text",
        item.get("text", ""),
        height=180,
        key=f"chunk-{key_prefix}-{item.get('id', '')}",
        label_visibility="collapsed",
    )


def _render_graph(item: dict[str, Any]) -> None:
    meta = item.get("metadata", {})
    st.markdown(
        " | ".join(
            part
            for part in [
                f"**{item.get('node_label', '')}:** {item.get('node_name', '')}",
                item.get("relationship", ""),
                f"**{item.get('neighbor_label', '')}:** {item.get('neighbor_name', '')}"
                if item.get("neighbor_name")
                else "",
                f"Page: {meta.get('pages') or meta.get('page', '')}",
            ]
            if part
        )
    )


def _clean_answer_text(answer: str) -> str:
    return re.split(r"\n\s*Sources\s*:", answer.strip(), maxsplit=1, flags=re.IGNORECASE)[0].strip()


def _render_sources(citations: list[dict[str, Any]]) -> None:
    seen: set[tuple[str, str, str]] = set()
    sources: list[dict[str, Any]] = []

    for citation in citations:
        chapter = str(citation.get("chapter") or "").strip()
        section = str(citation.get("section") or "").strip()
        page = str(citation.get("page") or "").strip()
        key = (chapter, section, page)
        if key in seen:
            continue
        seen.add(key)
        sources.append({"chapter": chapter, "section": section, "page": page})

    st.subheader("Sources Used")
    if not sources:
        st.caption("No source citations returned.")
        return

    for source in sources:
        st.markdown(
            "\n".join(
                [
                    f"- **Chapter:** {source['chapter'] or 'Not available'}",
                    f"  **Section:** {source['section'] or 'Not available'}",
                    f"  **Page(s):** {source['page'] or 'Not available'}",
                ]
            )
        )


def _render_retrieval_evidence(payload: dict[str, Any]) -> None:
    evidence = payload.get("evidence", {})
    debug = payload.get("debug", {})

    with st.expander("Retrieval Evidence", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Retrieved chunks", debug.get("retrieved_chunk_count", 0))
        col2.metric("Final chunks", debug.get("final_chunk_count", 0))
        col3.metric("Survived filtering", debug.get("chunks_survived_filtering_count", 0))
        col4.metric("Deduplicated", debug.get("deduplicated_chunk_count", 0))

        if debug.get("retrieval_query") and debug.get("retrieval_query") != debug.get("original_query"):
            st.caption(f"Normalized retrieval query: {debug.get('retrieval_query')}")

        st.caption(debug.get("score_threshold_note", ""))

        if evidence.get("graph_error"):
            st.caption(f"Graph retrieval note: {evidence['graph_error']}")

        semantic_tab, keyword_tab, graph_tab = st.tabs(
            ["Semantic Chunks", "Keyword Chunks", "Graph Nodes"]
        )
        with semantic_tab:
            for index, item in enumerate(evidence.get("semantic_chunks", [])):
                _render_chunk(item, f"semantic-{index}")
                st.divider()
        with keyword_tab:
            for index, item in enumerate(evidence.get("keyword_chunks", [])):
                _render_chunk(item, f"keyword-{index}")
                st.divider()
        with graph_tab:
            for item in evidence.get("graph_nodes", []):
                _render_graph(item)
                st.divider()


st.set_page_config(page_title="Vanco Hybrid RAG", layout="wide")
st.title("Vanco Hybrid RAG - NCERT Physics")

with st.sidebar:
    api_url = st.text_input("API URL", DEFAULT_API_URL)
    top_k = st.slider("Top K", min_value=1, max_value=20, value=5)
    st.divider()
    pdf_path = st.text_input("PDF path", "data/physics.pdf")
    reset_graph = st.checkbox("Reset Neo4j graph", value=False)
    if st.button("Run ingestion", type="secondary"):
        with st.spinner("Ingesting PDF and rebuilding indexes"):
            try:
                result = _post_json(
                    f"{api_url.rstrip('/')}/ingest",
                    {"pdf_path": pdf_path, "reset_graph": reset_graph},
                )
                st.success(result)
            except Exception as exc:
                st.error(str(exc))

question = st.text_area("Question", height=100, placeholder="Ask a question from the NCERT Physics PDF")
if st.button("Ask", type="primary", disabled=not question.strip()):
    with st.spinner("Retrieving evidence and generating grounded answer"):
        try:
            payload = _post_json(f"{api_url.rstrip('/')}/ask", {"question": question, "top_k": top_k})
        except Exception as exc:
            st.error(str(exc))
        else:
            st.subheader("Answer")
            st.markdown(_clean_answer_text(payload["answer"]))
            st.caption("&#10003; Generated from retrieved document evidence")
            _render_sources(payload.get("citations", []))
            st.caption(f"Latency: {payload.get('latency_ms', 0):.0f} ms")
            _render_retrieval_evidence(payload)
