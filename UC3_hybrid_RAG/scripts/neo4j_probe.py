"""Small Neo4j readiness helper used by start_backend.ps1.

Keeping this in a file avoids Windows PowerShell quoting issues with
multi-line `python -c` snippets.
"""

from __future__ import annotations

import argparse
import os
import sys

from neo4j import GraphDatabase


def _driver():
    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not uri or not username or not password:
        raise RuntimeError("NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set")
    return GraphDatabase.driver(uri, auth=(username, password))


def check_connectivity() -> int:
    driver = _driver()
    try:
        driver.verify_connectivity()
    finally:
        driver.close()
    return 0


def graph_count() -> int:
    source = os.getenv("SOURCE_NAME", "NCERT_Physics_Part1.pdf")
    database = os.getenv("NEO4J_DATABASE", "neo4j") or "neo4j"
    driver = _driver()
    try:
        with driver.session(database=database) as session:
            record = session.run(
                "MATCH (n {source: $source}) RETURN count(n) AS count",
                source=source,
            ).single()
            print(record["count"] if record else 0)
    finally:
        driver.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["connect", "count"])
    args = parser.parse_args()

    try:
        if args.mode == "connect":
            return check_connectivity()
        return graph_count()
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
