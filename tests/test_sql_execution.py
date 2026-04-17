import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def playbooks_dir(tmp_path):
    index_data = {
        "entries": [
            {
                "slug": "test-query",
                "name": "Test Query",
                "purpose": "Test purpose",
                "status": "draft",
                "execution_location": "Redshift",
                "tables": ["schema.test_table"],
            }
        ]
    }
    (tmp_path / "INDEX.json").write_text(json.dumps(index_data))
    slug_dir = tmp_path / "test-query"
    slug_dir.mkdir()
    (slug_dir / "test-query__raw.sql").write_text("SELECT * FROM schema.test_table LIMIT 10;")
    return tmp_path


def test_list_playbooks(playbooks_dir):
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir=str(playbooks_dir), results_dir=str(playbooks_dir / "results"))
    result = tools.list_playbooks()
    parsed = json.loads(result)
    assert len(parsed) == 1
    assert parsed[0]["slug"] == "test-query"
    assert parsed[0]["purpose"] == "Test purpose"


def test_run_query_rejects_insert():
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir="/tmp", results_dir="/tmp/results")
    result = tools.run_query("INSERT INTO table VALUES (1, 2)")
    assert "error" in result.lower() or "forbidden" in result.lower()


def test_run_query_rejects_drop():
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir="/tmp", results_dir="/tmp/results")
    result = tools.run_query("DROP TABLE schema.important")
    assert "error" in result.lower() or "forbidden" in result.lower()


def test_run_query_rejects_delete():
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir="/tmp", results_dir="/tmp/results")
    result = tools.run_query("DELETE FROM schema.test WHERE id = 1")
    assert "error" in result.lower() or "forbidden" in result.lower()


def test_run_query_accepts_select():
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir="/tmp", results_dir="/tmp/results")
    with patch("toolkits.sql_execution._get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchmany.return_value = [("a", "b"), ("c", "d")]
        mock_conn.return_value.cursor.return_value = mock_cursor

        result = tools.run_query("SELECT col1, col2 FROM schema.test LIMIT 10")
        assert "col1" in result
        assert "col2" in result


def test_run_playbook_finds_slug(playbooks_dir):
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir=str(playbooks_dir), results_dir=str(playbooks_dir / "results"))
    with patch("toolkits.sql_execution._get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.description = [("col1",)]
        mock_cursor.fetchmany.return_value = [("val",)]
        mock_conn.return_value.cursor.return_value = mock_cursor

        result = tools.run_playbook("test-query")
        assert "col1" in result


def test_run_playbook_not_found(playbooks_dir):
    from toolkits.sql_execution import SQLExecutionTools
    tools = SQLExecutionTools(playbooks_dir=str(playbooks_dir), results_dir=str(playbooks_dir / "results"))
    result = tools.run_playbook("nonexistent-slug")
    assert "not found" in result.lower()
