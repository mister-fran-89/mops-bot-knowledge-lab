import json
import pytest
from pathlib import Path


@pytest.fixture
def playbooks_dir(tmp_path):
    slug_dir = tmp_path / "test-playbook"
    slug_dir.mkdir()
    playbook_json = {
        "header": {"name": "Test Playbook"},
        "objects_referenced": {"tables": ["schema.orders", "schema.customers"]},
        "ctes": [{"cte": "base_orders", "purpose": "Filter orders"}],
    }
    (slug_dir / "test-playbook__playbook.json").write_text(json.dumps(playbook_json))
    return tmp_path


def test_compare_sql_finds_overlap(playbooks_dir):
    from toolkits.sql_comparison import SQLComparisonTools
    tools = SQLComparisonTools(playbooks_dir=str(playbooks_dir))
    sql = "SELECT * FROM schema.orders JOIN schema.customers ON o.id = c.order_id"
    result = tools.compare_sql(sql)
    parsed = json.loads(result)
    assert len(parsed) >= 1
    assert parsed[0]["slug"] == "test-playbook"
    assert parsed[0]["similarity_score"] > 0


def test_compare_sql_no_overlap(playbooks_dir):
    from toolkits.sql_comparison import SQLComparisonTools
    tools = SQLComparisonTools(playbooks_dir=str(playbooks_dir))
    sql = "SELECT * FROM completely_different_table"
    result = tools.compare_sql(sql)
    parsed = json.loads(result)
    for entry in parsed:
        assert entry["similarity_score"] < 0.5


def test_compare_sql_extracts_ctes(playbooks_dir):
    from toolkits.sql_comparison import SQLComparisonTools
    tools = SQLComparisonTools(playbooks_dir=str(playbooks_dir))
    sql = "WITH base_orders AS (SELECT * FROM schema.orders) SELECT * FROM base_orders"
    result = tools.compare_sql(sql)
    parsed = json.loads(result)
    assert len(parsed) >= 1
    assert parsed[0]["similarity_score"] > 0.3
