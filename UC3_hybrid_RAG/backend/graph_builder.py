"""Neo4j graph construction for chapters, topics, concepts, formulas, and definitions."""

from __future__ import annotations

import itertools
import re
from typing import Any, Iterable

from .config import Settings
from .logging_utils import get_logger
from .schemas import DocumentChunk


LOGGER = get_logger(__name__)

CONCEPT_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+(?:and|of|in|on|[A-Z][a-z]+)){0,4}\b")
FORMULA_LINE_RE = re.compile(r"(?m)^(?=.{3,180}$).*(=|\\frac|\\sqrt|proportional to).*$")
DEFINITION_RE = re.compile(
    r"(?P<term>[A-Z][A-Za-z0-9 ]{2,60})\s+"
    r"(?P<verb>is|are|is called|are called|is defined as|are defined as)\s+"
    r"(?P<body>[^.]{10,240})\.",
    re.IGNORECASE,
)
STOP_CONCEPTS = {
    "Page",
    "Chapter",
    "Example",
    "Exercise",
    "Solution",
    "Answer",
    "Fig",
    "Table",
}


class GraphConfigError(RuntimeError):
    pass


def _key(label: str, name: str, source: str) -> str:
    return f"{label}:{source}:{name.strip().lower()}"


def _concepts(text: str, limit: int = 12) -> list[str]:
    found: list[str] = []
    for match in CONCEPT_RE.finditer(text):
        concept = match.group(0).strip()
        if concept in STOP_CONCEPTS or len(concept) < 4:
            continue
        if concept.lower().startswith("page "):
            continue
        if concept not in found:
            found.append(concept)
        if len(found) >= limit:
            break
    return found


def _formulas(text: str, limit: int = 8) -> list[str]:
    formulas: list[str] = []
    for match in FORMULA_LINE_RE.finditer(text):
        formula = re.sub(r"\s+", " ", match.group(0)).strip()
        if formula and formula not in formulas:
            formulas.append(formula)
        if len(formulas) >= limit:
            break
    return formulas


def _definitions(text: str, limit: int = 8) -> list[tuple[str, str]]:
    definitions: list[tuple[str, str]] = []
    clean = re.sub(r"\s+", " ", text)
    for match in DEFINITION_RE.finditer(clean):
        term = match.group("term").strip()
        definition = f"{term} {match.group('verb')} {match.group('body').strip()}."
        definitions.append((term, definition))
        if len(definitions) >= limit:
            break
    return definitions


def _batched(rows: list[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    for index in range(0, len(rows), batch_size):
        yield rows[index : index + batch_size]


def _dedupe(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        identity = tuple(row[key] for key in keys)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(row)
    return unique


class Neo4jGraphBuilder:
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

    def ensure_schema(self) -> None:
        constraints = [
            "CREATE CONSTRAINT chapter_key IF NOT EXISTS FOR (n:Chapter) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT topic_key IF NOT EXISTS FOR (n:Topic) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT concept_key IF NOT EXISTS FOR (n:Concept) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT formula_key IF NOT EXISTS FOR (n:Formula) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT definition_key IF NOT EXISTS FOR (n:Definition) REQUIRE n.key IS UNIQUE",
        ]
        with self.driver.session(database=self.settings.neo4j_database) as session:
            for statement in constraints:
                session.run(statement).consume()

    def reset_source(self, source: str) -> None:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run("MATCH (n {source: $source}) DETACH DELETE n", source=source).consume()

    def build(self, chunks: Iterable[DocumentChunk], reset: bool = False) -> None:
        chunks = list(chunks)
        if not chunks:
            LOGGER.warning("No chunks supplied to graph builder")
            return

        self.ensure_schema()
        if reset:
            self.reset_source(str(chunks[0].metadata.get("source", self.settings.source_name)))

        LOGGER.info("Building Neo4j graph from %s chunks", len(chunks))
        graph_rows = self._prepare_graph_rows(chunks)
        LOGGER.info(
            "Prepared Neo4j graph rows: topics=%s concepts=%s formulas=%s definitions=%s "
            "uses_formula=%s related_to=%s depends_on=%s",
            len(graph_rows["topics"]),
            len(graph_rows["concepts"]),
            len(graph_rows["formulas"]),
            len(graph_rows["definitions"]),
            len(graph_rows["uses_formula"]),
            len(graph_rows["related_to"]),
            len(graph_rows["depends_on"]),
        )
        with self.driver.session(database=self.settings.neo4j_database) as session:
            self._write_graph_rows(session, graph_rows)
        LOGGER.info("Neo4j graph build complete")

    def _prepare_graph_rows(self, chunks: list[DocumentChunk]) -> dict[str, list[dict[str, Any]]]:
        graph_rows: dict[str, list[dict[str, Any]]] = {
            "topics": [],
            "concepts": [],
            "formulas": [],
            "uses_formula": [],
            "definitions": [],
            "related_to": [],
            "depends_on": [],
        }

        for chunk in chunks:
            chunk_rows = self._rows_for_chunk(chunk)
            for key, rows in chunk_rows.items():
                graph_rows[key].extend(rows)

        return {
            "topics": _dedupe(graph_rows["topics"], ("topic_key",)),
            "concepts": _dedupe(graph_rows["concepts"], ("topic_key", "concept_key")),
            "formulas": _dedupe(graph_rows["formulas"], ("topic_key", "formula_key")),
            "uses_formula": _dedupe(graph_rows["uses_formula"], ("concept_key", "formula_key")),
            "definitions": _dedupe(graph_rows["definitions"], ("topic_key", "definition_key")),
            "related_to": _dedupe(graph_rows["related_to"], ("left_key", "right_key")),
            "depends_on": _dedupe(graph_rows["depends_on"], ("left_key", "right_key")),
        }

    def _rows_for_chunk(self, chunk: DocumentChunk) -> dict[str, list[dict[str, Any]]]:
        metadata = chunk.metadata
        source = str(metadata.get("source", self.settings.source_name))
        chapter = str(metadata.get("chapter", "Unknown Chapter"))
        section = str(metadata.get("section", "Unknown Section"))
        page = int(metadata.get("page", 0))
        pages = str(metadata.get("pages", page))
        topic_key = _key("Topic", f"{chapter}:{section}", source)

        concepts = _concepts(f"{chapter}\n{section}\n{chunk.text}")
        formulas = _formulas(chunk.text)
        definitions = _definitions(chunk.text)

        rows: dict[str, list[dict[str, Any]]] = {
            "topics": [
                {
                    "chapter_key": _key("Chapter", chapter, source),
                    "topic_key": topic_key,
                    "chapter": chapter,
                    "section": section,
                    "source": source,
                    "page": page,
                    "pages": pages,
                }
            ],
            "concepts": [],
            "formulas": [],
            "uses_formula": [],
            "definitions": [],
            "related_to": [],
            "depends_on": [],
        }

        for concept in concepts:
            rows["concepts"].append(
                {
                    "topic_key": topic_key,
                    "concept_key": _key("Concept", concept, source),
                    "concept": concept,
                    "source": source,
                    "chapter": chapter,
                    "section": section,
                    "page": page,
                    "pages": pages,
                }
            )

        for formula in formulas:
            formula_key = _key("Formula", formula, source)
            rows["formulas"].append(
                {
                    "topic_key": topic_key,
                    "formula_key": formula_key,
                    "formula": formula,
                    "source": source,
                    "chapter": chapter,
                    "section": section,
                    "page": page,
                    "pages": pages,
                }
            )
            for concept in concepts[:5]:
                rows["uses_formula"].append(
                    {
                        "concept_key": _key("Concept", concept, source),
                        "formula_key": formula_key,
                    }
                )

        for term, definition in definitions:
            rows["definitions"].append(
                {
                    "topic_key": topic_key,
                    "definition_key": _key("Definition", definition[:120], source),
                    "concept_key": _key("Concept", term, source),
                    "term": term,
                    "definition": definition,
                    "source": source,
                    "chapter": chapter,
                    "section": section,
                    "page": page,
                    "pages": pages,
                }
            )

        for left, right in itertools.combinations(concepts[:6], 2):
            rows["related_to"].append(
                {
                    "left_key": _key("Concept", left, source),
                    "right_key": _key("Concept", right, source),
                }
            )

        depends_match = re.search(r"([A-Z][A-Za-z ]{2,50})\s+depends on\s+([A-Z][A-Za-z ]{2,50})", chunk.text)
        if depends_match:
            left = depends_match.group(1).strip()
            right = depends_match.group(2).strip()
            rows["depends_on"].append(
                {
                    "left_key": _key("Concept", left, source),
                    "right_key": _key("Concept", right, source),
                    "left": left,
                    "right": right,
                    "source": source,
                }
            )

        return rows

    def _write_graph_rows(self, session, graph_rows: dict[str, list[dict[str, Any]]]) -> None:
        batch_size = 500
        statements = [
            (
                "topics",
                """
                UNWIND $rows AS row
                MERGE (chapter:Chapter {key: row.chapter_key})
                SET chapter.name = row.chapter, chapter.source = row.source
                MERGE (topic:Topic {key: row.topic_key})
                SET topic.name = row.section, topic.source = row.source, topic.chapter = row.chapter,
                    topic.page = row.page, topic.pages = row.pages
                MERGE (chapter)-[:CONTAINS]->(topic)
                """,
            ),
            (
                "concepts",
                """
                UNWIND $rows AS row
                MATCH (topic:Topic {key: row.topic_key})
                MERGE (concept:Concept {key: row.concept_key})
                SET concept.name = row.concept, concept.source = row.source, concept.chapter = row.chapter,
                    concept.section = row.section, concept.page = row.page, concept.pages = row.pages
                MERGE (topic)-[:EXPLAINS]->(concept)
                """,
            ),
            (
                "formulas",
                """
                UNWIND $rows AS row
                MATCH (topic:Topic {key: row.topic_key})
                MERGE (formula:Formula {key: row.formula_key})
                SET formula.name = row.formula, formula.expression = row.formula, formula.source = row.source,
                    formula.chapter = row.chapter, formula.section = row.section, formula.page = row.page,
                    formula.pages = row.pages
                MERGE (topic)-[:CONTAINS]->(formula)
                """,
            ),
            (
                "uses_formula",
                """
                UNWIND $rows AS row
                MATCH (concept:Concept {key: row.concept_key})
                MATCH (formula:Formula {key: row.formula_key})
                MERGE (concept)-[:USES_FORMULA]->(formula)
                """,
            ),
            (
                "definitions",
                """
                UNWIND $rows AS row
                MATCH (topic:Topic {key: row.topic_key})
                MERGE (definition:Definition {key: row.definition_key})
                SET definition.name = row.term, definition.text = row.definition, definition.source = row.source,
                    definition.chapter = row.chapter, definition.section = row.section, definition.page = row.page,
                    definition.pages = row.pages
                MERGE (topic)-[:CONTAINS]->(definition)
                MERGE (topic)-[:EXPLAINS]->(definition)
                MERGE (concept:Concept {key: row.concept_key})
                SET concept.name = row.term, concept.source = row.source, concept.chapter = row.chapter,
                    concept.section = row.section, concept.page = row.page, concept.pages = row.pages
                MERGE (concept)-[:DEFINED_BY]->(definition)
                """,
            ),
            (
                "related_to",
                """
                UNWIND $rows AS row
                MATCH (left:Concept {key: row.left_key})
                MATCH (right:Concept {key: row.right_key})
                MERGE (left)-[:RELATED_TO]->(right)
                """,
            ),
            (
                "depends_on",
                """
                UNWIND $rows AS row
                MERGE (left:Concept {key: row.left_key})
                SET left.name = row.left, left.source = row.source
                MERGE (right:Concept {key: row.right_key})
                SET right.name = row.right, right.source = row.source
                MERGE (left)-[:DEPENDS_ON]->(right)
                """,
            ),
        ]

        for label, statement in statements:
            rows = graph_rows[label]
            if not rows:
                continue
            total_batches = (len(rows) + batch_size - 1) // batch_size
            LOGGER.info("Writing %s Neo4j %s rows in %s batches", len(rows), label, total_batches)
            for index, batch in enumerate(_batched(rows, batch_size), start=1):
                session.run(statement, rows=batch).consume()
                LOGGER.info("Wrote Neo4j %s batch %s/%s", label, index, total_batches)
