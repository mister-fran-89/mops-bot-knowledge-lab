"""PlaybookSearchTools — Agno Toolkit for searching the SQL playbook corpus.

Ports logic from:
  - engines/sql-archivist-engine/tools/search_index.py
  - engines/sql-archivist-engine/tools/search_playbooks.py
  - engines/sql-archivist-engine/tools/score_match.py
"""

import json
import re
from pathlib import Path
from agno.tools import Toolkit


def _tokenize(text):
    if not text:
        return set()
    parts = re.split(r'[\s_.\\-]+', str(text).lower())
    return {p for p in parts if p}


def _token_overlap(query_tokens, target_tokens):
    if not query_tokens:
        return 0.0
    return len(query_tokens & target_tokens) / len(query_tokens)


def _match_field(entry, field_name, query_text):
    value = entry.get(field_name)
    if value is None:
        return {"field": field_name, "matched": False, "score": 0.0}
    query_tokens = _tokenize(query_text)
    if isinstance(value, list):
        target_tokens = _tokenize(" ".join(str(v) for v in value))
    else:
        target_tokens = _tokenize(str(value))
    score = _token_overlap(query_tokens, target_tokens)
    return {"field": field_name, "matched": score > 0.0, "score": round(score, 4)}


def _classify_strength(query_text, actual_text):
    qt = _tokenize(query_text)
    at = _tokenize(str(actual_text) if actual_text else "")
    overlap = _token_overlap(qt, at)
    if overlap >= 0.75:
        return "strong"
    elif overlap >= 0.25:
        return "partial"
    return "none"


_STRENGTH_WEIGHT = {"strong": 1.0, "partial": 0.5, "none": 0.0}


def _resolve_field_value(playbook, field_name):
    header = playbook.get("header", {})
    if field_name in header:
        val = header[field_name]
        if isinstance(val, list):
            return " ".join(str(v) for v in val)
        return str(val)
    if field_name == "objects_referenced":
        obj = playbook.get("objects_referenced", {})
        parts = []
        for key in ("tables", "views", "functions", "procedures"):
            parts.extend(obj.get(key, []))
        return " ".join(parts) if parts else None
    if field_name == "ctes":
        ctes = playbook.get("ctes", [])
        parts = []
        for cte in ctes:
            parts.append(cte.get("cte", ""))
            parts.append(cte.get("purpose", ""))
        return " ".join(parts) if parts else None
    if field_name in playbook:
        val = playbook[field_name]
        if isinstance(val, dict):
            return " ".join(str(v) for v in val.values())
        if isinstance(val, list):
            return " ".join(str(v) for v in val)
        return str(val)
    exec_loc = playbook.get("execution_location", {})
    if isinstance(exec_loc, dict) and field_name in exec_loc:
        return str(exec_loc[field_name])
    return None


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


class PlaybookSearchTools(Toolkit):
    def __init__(self, playbooks_dir: str):
        self.playbooks_dir = playbooks_dir
        tools = [
            self.search_index,
            self.search_playbooks_deep,
            self.score_match,
            self.get_playbook_detail,
        ]
        super().__init__(name="playbook_search", tools=tools)

    def search_index(self, field_queries: str) -> str:
        """Search INDEX.json by field-value pairs. Fast metadata search.

        Args:
            field_queries: JSON array of [field_name, query_text] pairs.
                Example: '[["purpose", "monthly metrics"], ["execution_location", "Redshift"]]'
        """
        pairs = json.loads(field_queries)
        index_path = Path(self.playbooks_dir) / "INDEX.json"
        if not index_path.is_file():
            return json.dumps({"error": f"INDEX.json not found at {index_path}"})
        with open(index_path, encoding="utf-8") as f:
            index_data = json.load(f)

        entries = index_data.get("entries", [])
        if not pairs:
            return json.dumps([])

        weight = 1.0 / len(pairs)
        results = []
        for entry in entries:
            total = 0.0
            field_scores = []
            for field_name, query_text in pairs:
                fs = _match_field(entry, field_name, query_text)
                field_scores.append(fs)
                total += weight * fs["score"]
            total = round(total, 4)
            if total >= 0.01:
                results.append({
                    "slug": entry.get("slug"),
                    "name": entry.get("name"),
                    "purpose": entry.get("purpose"),
                    "execution_location": entry.get("execution_location"),
                    "total_score": total,
                    "field_scores": field_scores,
                })
        results.sort(key=lambda r: r["total_score"], reverse=True)
        return json.dumps(results[:10])

    def search_playbooks_deep(self, field_queries: str) -> str:
        """Deep search across playbook.json files for fields not in INDEX.json.

        Searches: ctes, objects_referenced, joins, filters, final_select_columns, warnings, limitations.

        Args:
            field_queries: JSON array of [field_name, query_text] pairs.
                Example: '[["ctes", "base_data"], ["objects_referenced", "core_maker"]]'
        """
        pairs = json.loads(field_queries)
        playbooks = _discover_playbooks(self.playbooks_dir)
        if not pairs:
            return json.dumps([])

        results = []
        for pb in playbooks:
            field_scores = []
            weight = 1.0 / len(pairs)
            total = 0.0
            for field_name, query_text in pairs:
                actual = _resolve_field_value(pb["data"], field_name)
                strength = _classify_strength(query_text, actual) if actual else "none"
                score = _STRENGTH_WEIGHT[strength]
                field_scores.append({"field": field_name, "strength": strength, "score": score})
                total += weight * score
            total = round(total, 4)
            if total >= 0.01:
                results.append({
                    "slug": pb["slug"],
                    "name": pb["data"].get("header", {}).get("name", "Unknown"),
                    "total_score": total,
                    "field_scores": field_scores,
                })
        results.sort(key=lambda r: r["total_score"], reverse=True)
        return json.dumps(results[:10])

    def score_match(self, slug: str, field_queries: str) -> str:
        """Score a specific playbook against decomposed query fields.

        Args:
            slug: The playbook slug to score.
            field_queries: JSON array of [field_name, query_text] pairs.
        """
        pb_path = Path(self.playbooks_dir) / slug / f"{slug}__playbook.json"
        if not pb_path.is_file():
            return json.dumps({"error": f"playbook.json not found for slug '{slug}'"})
        with open(pb_path, encoding="utf-8") as f:
            playbook = json.load(f)

        pairs = json.loads(field_queries)
        field_scores = []
        for field_name, query_text in pairs:
            actual = _resolve_field_value(playbook, field_name)
            strength = _classify_strength(query_text, actual) if actual else "none"
            qt = _tokenize(query_text)
            at = _tokenize(str(actual) if actual else "")
            overlap = _token_overlap(qt, at)
            field_scores.append({
                "field": field_name,
                "query": query_text,
                "actual": actual,
                "strength": strength,
                "matched": overlap > 0.0,
                "overlap": round(overlap, 4),
            })

        if field_scores:
            weight = 1.0 / len(field_scores)
            total = sum(weight * _STRENGTH_WEIGHT[fs["strength"]] for fs in field_scores)
        else:
            total = 0.0

        return json.dumps({
            "slug": slug,
            "name": playbook.get("header", {}).get("name", "Unknown"),
            "total_score": round(total, 4),
            "field_scores": field_scores,
        })

    def get_playbook_detail(self, slug: str) -> str:
        """Get full documentation and metadata for a specific playbook.

        Args:
            slug: The playbook slug.
        """
        slug_dir = Path(self.playbooks_dir) / slug
        if not slug_dir.is_dir():
            return f"Playbook not found: slug '{slug}' does not exist in {self.playbooks_dir}"

        parts = []

        md_path = slug_dir / f"{slug}__playbook.md"
        if md_path.is_file():
            parts.append("## Documentation\n")
            parts.append(md_path.read_text(encoding="utf-8"))

        json_path = slug_dir / f"{slug}__playbook.json"
        if json_path.is_file():
            with open(json_path, encoding="utf-8") as f:
                metadata = json.load(f)
            parts.append("\n## Metadata\n")
            parts.append(json.dumps(metadata, indent=2))

        if not parts:
            return f"Playbook '{slug}' directory exists but contains no artifacts."

        return "\n".join(parts)
