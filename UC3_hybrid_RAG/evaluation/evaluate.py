"""Sample evaluation runner for the Hybrid RAG API."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
QUESTIONS = [
    "What is Coulomb's law?",
    "How is electric field defined?",
    "State Gauss's law.",
    "What is the formula for electric potential energy of two point charges?",
    "Compare conductors and insulators.",
    "What does the NCERT document say about black holes?",
]


def main() -> None:
    results = []
    for question in QUESTIONS:
        started = time.perf_counter()
        response = requests.post(
            f"{API_BASE_URL.rstrip('/')}/ask",
            json={"question": question, "top_k": 5},
            timeout=180,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        response.raise_for_status()
        payload = response.json()
        results.append(
            {
                "question": question,
                "latency_ms": latency_ms,
                "answer": payload.get("answer"),
                "citations": payload.get("citations"),
                "semantic_evidence_count": len(payload.get("evidence", {}).get("semantic_chunks", [])),
                "keyword_evidence_count": len(payload.get("evidence", {}).get("keyword_chunks", [])),
                "graph_evidence_count": len(payload.get("evidence", {}).get("graph_nodes", [])),
                "evidence": payload.get("evidence"),
            }
        )

    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path("logs") / f"evaluation_{timestamp}.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved evaluation results to {output_path}")


if __name__ == "__main__":
    main()

