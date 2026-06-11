"""Neo4j graph retrieval used during question answering."""

from __future__ import annotations

import re

from .config import Settings
from .graph_builder import GraphConfigError
from .logging_utils import get_logger
from .schemas import GraphEvidence


LOGGER = get_logger(__name__)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")


def _terms(query: str) -> list[str]:
    terms: list[str] = []
    for token in TOKEN_RE.findall(query.lower()):
        if token in {"what", "which", "from", "with", "that", "this", "when", "where", "does"}:
            continue
        if token not in terms:
            terms.append(token)
    return terms[:12]


class Neo4jGraphRetriever:
    def __init__(self, settings: Settings) -> None:
        if not (settings.neo4j_uri and settings.neo4j_username and settings.neo4j_password):
            raise GraphConfigError("NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set")

        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("neo4j Python driver is required for graph retrieval") from exc

        self.settings = settings
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    def close(self) -> None:
        self.driver.close()

    def query(self, query: str, top_k: int) -> list[GraphEvidence]:
        terms = _terms(query)
        if not terms:
            return []

        LOGGER.info("Running graph retrieval top_k=%s terms=%s", top_k, terms)
        cypher = """
        MATCH (n)
        WHERE n.source = $source
          AND any(term IN $terms WHERE
            toLower(coalesce(n.name, '')) CONTAINS term OR
            toLower(coalesce(n.text, '')) CONTAINS term OR
            toLower(coalesce(n.expression, '')) CONTAINS term)
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN labels(n) AS node_labels, n AS node, type(r) AS rel,
               labels(m) AS neighbor_labels, m AS neighbor
        LIMIT $limit
        """
        results: list[GraphEvidence] = []
        with self.driver.session(database=self.settings.neo4j_database) as session:
            records = session.run(cypher, source=self.settings.source_name, terms=terms, limit=top_k * 4)
            for record in records:
                node = dict(record["node"])
                neighbor = dict(record["neighbor"]) if record["neighbor"] is not None else {}
                node_label = (record["node_labels"] or ["Node"])[0]
                neighbor_label = (record["neighbor_labels"] or ["Node"])[0] if neighbor else ""
                metadata = {
                    "page": node.get("page") or neighbor.get("page") or 0,
                    "pages": node.get("pages") or neighbor.get("pages") or "",
                    "chapter": node.get("chapter") or neighbor.get("chapter") or "",
                    "section": node.get("section") or neighbor.get("section") or "",
                    "source": node.get("source") or neighbor.get("source") or self.settings.source_name,
                }
                results.append(
                    GraphEvidence(
                        node_label=node_label,
                        node_name=str(node.get("name") or node.get("expression") or ""),
                        relationship=str(record["rel"] or ""),
                        neighbor_label=neighbor_label,
                        neighbor_name=str(neighbor.get("name") or neighbor.get("expression") or ""),
                        metadata=metadata,
                        score=1.0,
                    )
                )
                if len(results) >= top_k:
                    break
        return results

