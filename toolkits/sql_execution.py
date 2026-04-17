"""SQLExecutionTools — Execute SQL against Redshift.

Ports logic from: engines/sql-execution-engine/executor.py
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from agno.tools import Toolkit


_FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
    "ALTER", "TRUNCATE", "GRANT", "REVOKE",
]


def _strip_sql_comments(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _validate_read_only(sql):
    cleaned = _strip_sql_comments(sql).strip()
    if not cleaned:
        return "SQL is empty after removing comments."
    first_word = re.split(r"\s+", cleaned)[0].upper()
    if first_word not in ("SELECT", "WITH"):
        return f"SQL must start with SELECT or WITH. Found: {first_word}"
    upper_cleaned = cleaned.upper()
    for keyword in _FORBIDDEN_KEYWORDS:
        pattern = r"\b" + keyword + r"\b"
        if re.search(pattern, upper_cleaned):
            return f"Forbidden keyword detected: {keyword}. Only read-only queries are allowed."
    return None


def _get_connection():
    import psycopg2
    required_vars = ["REDSHIFT_HOST", "REDSHIFT_PORT", "REDSHIFT_DB",
                     "REDSHIFT_USER", "REDSHIFT_PASSWORD"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return psycopg2.connect(
        host=os.environ["REDSHIFT_HOST"],
        port=int(os.environ["REDSHIFT_PORT"]),
        dbname=os.environ["REDSHIFT_DB"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )


def _execute_and_format(sql):
    validation_error = _validate_read_only(sql)
    if validation_error:
        return f"**Error:** {validation_error}"

    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 90000;")
        cur.execute(sql)

        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows_all = cur.fetchmany(11)
        truncated = len(rows_all) > 10
        rows = rows_all[:10]

        if truncated:
            remaining = 0
            while True:
                batch = cur.fetchmany(1000)
                if not batch:
                    break
                remaining += len(batch)
            row_count = 10 + 1 + remaining
        else:
            row_count = len(rows)

        rows_str = [[str(v) if v is not None else None for v in row] for row in rows]

        lines = []
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join("---" for _ in columns) + " |")
        for row in rows_str:
            lines.append("| " + " | ".join(v if v is not None else "NULL" for v in row) + " |")

        summary = f"\n\n**{row_count} rows total**"
        if truncated:
            summary += " (showing first 10)"

        return "\n".join(lines) + summary

    except Exception as e:
        return f"**Error:** Query execution failed: {e}"
    finally:
        conn.close()


class SQLExecutionTools(Toolkit):
    def __init__(self, playbooks_dir: str, results_dir: str = "./data/results"):
        self.playbooks_dir = playbooks_dir
        self.results_dir = results_dir
        tools = [
            self.list_playbooks,
            self.run_query,
            self.run_playbook,
            self.export_csv,
        ]
        super().__init__(name="sql_execution", tools=tools)

    def list_playbooks(self) -> str:
        """List all available SQL playbooks with their purpose and metadata."""
        index_path = Path(self.playbooks_dir) / "INDEX.json"
        if not index_path.is_file():
            return json.dumps({"error": "INDEX.json not found"})
        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", [])
        result = []
        for entry in entries:
            result.append({
                "slug": entry.get("slug"),
                "name": entry.get("name"),
                "purpose": entry.get("purpose"),
                "status": entry.get("status"),
                "execution_location": entry.get("execution_location"),
                "tables": entry.get("tables", []),
            })
        return json.dumps(result, indent=2)

    def run_query(self, sql: str) -> str:
        """Execute a read-only SQL query against Redshift and return results as a markdown table.

        Only SELECT and WITH queries are allowed. 90-second timeout. Shows first 10 rows.

        Args:
            sql: The SQL query to execute. Must start with SELECT or WITH.
        """
        validation_error = _validate_read_only(sql)
        if validation_error:
            return f"**Error:** {validation_error}"
        return _execute_and_format(sql)

    def run_playbook(self, slug: str) -> str:
        """Execute a playbook's SQL script against Redshift.

        Args:
            slug: The playbook slug. The raw.sql file will be looked up and executed.
        """
        sql_path = Path(self.playbooks_dir) / slug / f"{slug}__raw.sql"
        if not sql_path.is_file():
            return f"**Error:** Playbook not found: no raw.sql for slug '{slug}'"
        sql = sql_path.read_text(encoding="utf-8")
        return _execute_and_format(sql)

    def export_csv(self, sql: str, slug: str = "adhoc") -> str:
        """Execute a query and export full results to CSV.

        Args:
            sql: The SQL query to execute.
            slug: Name for the output folder (default: 'adhoc').
        """
        validation_error = _validate_read_only(sql)
        if validation_error:
            return f"**Error:** {validation_error}"

        try:
            import pandas as pd
        except ImportError:
            return "**Error:** pandas not installed."

        conn = _get_connection()
        try:
            df = pd.read_sql(sql, conn)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = Path(self.results_dir) / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{slug}_{timestamp}.csv"
            df.to_csv(out_file, index=False)
            return f"Exported {len(df)} rows to `{out_file}`"
        except Exception as e:
            return f"**Error:** CSV export failed: {e}"
        finally:
            conn.close()
