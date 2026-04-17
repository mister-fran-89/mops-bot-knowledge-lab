"""SQLComparisonTools — Structural SQL comparison for duplicate detection.

Ports logic from: engines/sql-archivist-engine/tools/compare_sql.py
"""

import json
import re
from pathlib import Path
from agno.tools import Toolkit


def _strip_sql_comments(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _extract_table_references(sql):
    cleaned = _strip_sql_comments(sql)
    tables = set()
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*){0,2})'
    for match in re.finditer(pattern, cleaned, re.IGNORECASE):
        tables.add(match.group(1).lower())
    return tables


def _extract_cte_names(sql):
    cleaned = _strip_sql_comments(sql)
    ctes = set()
    pattern = r'(?:WITH|,)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\('
    for match in re.finditer(pattern, cleaned, re.IGNORECASE):
        ctes.add(match.group(1).lower())
    return ctes


def _extract_structural_signature(sql):
    tables = _extract_table_references(sql)
    cte_names = _extract_cte_names(sql)
    real_tables = tables - cte_names
    return {"tables": real_tables, "cte_names": cte_names, "all_elements": real_tables | cte_names}


def _get_playbook_elements(playbook_data):
    elements = set()
    obj_ref = playbook_data.get("objects_referenced", {})
    for table in obj_ref.get("tables", []):
        elements.add(table.lower())
    for cte in playbook_data.get("ctes", []):
        cte_name = cte.get("cte", "")
        if cte_name:
            elements.add(cte_name.lower())
    return elements


def _jaccard_similarity(set_a, set_b):
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _discover_playbooks(playbooks_dir):
    playbooks_dir = Path(playbooks_dir)
    results = []
    for slug_dir in sorted(playbooks_dir.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name
        pb_file = slug_dir / f"{slug}__playbook.json"
        if pb_file.is_file():
            with open(pb_file, encoding="utf-8") as f:
                data = json.load(f)
            results.append({"slug": slug, "data": data})
    return results


class SQLComparisonTools(Toolkit):
    def __init__(self, playbooks_dir: str):
        self.playbooks_dir = playbooks_dir
        tools = [self.compare_sql]
        super().__init__(name="sql_comparison", tools=tools)

    def compare_sql(self, sql: str) -> str:
        """Compare raw SQL against all existing playbooks using structural similarity.

        Extracts tables and CTE names from the SQL, then computes Jaccard similarity
        against each playbook's objects_referenced and ctes.

        Args:
            sql: Raw SQL to compare against the playbook corpus.
        """
        signature = _extract_structural_signature(sql)
        sql_elements = signature["all_elements"]

        if not sql_elements:
            return json.dumps([])

        playbooks = _discover_playbooks(self.playbooks_dir)
        results = []

        for pb in playbooks:
            pb_elements = _get_playbook_elements(pb["data"])
            similarity = _jaccard_similarity(sql_elements, pb_elements)

            if similarity >= 0.01:
                shared = sql_elements & pb_elements
                sql_only = sql_elements - pb_elements
                pb_only = pb_elements - sql_elements
                results.append({
                    "slug": pb["slug"],
                    "name": pb["data"].get("header", {}).get("name", "Unknown"),
                    "similarity_score": round(similarity, 4),
                    "overlap_details": {
                        "shared_elements": sorted(shared),
                        "sql_only_elements": sorted(sql_only),
                        "playbook_only_elements": sorted(pb_only),
                    },
                })

        results.sort(key=lambda r: r["similarity_score"], reverse=True)
        return json.dumps(results)
