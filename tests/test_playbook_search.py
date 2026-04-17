import json
import pytest
from pathlib import Path


@pytest.fixture
def playbooks_dir(tmp_path):
    """Create a minimal playbook structure for testing."""
    index_data = {
        "engine_name": "SQL Librarian Engine",
        "engine_version": "v1",
        "last_updated": "2026-04-17",
        "total_entries": 1,
        "entries": [
            {
                "slug": "test-playbook",
                "name": "Test Playbook",
                "path": "playbooks/test-playbook",
                "status": "draft",
                "confidence": "high",
                "execution_location": "Redshift",
                "purpose": "Monthly metrics for supplier accounts",
                "tables": ["analytics_bi_viz.core_maker_taker_uuid"],
            }
        ],
    }
    index_path = tmp_path / "INDEX.json"
    index_path.write_text(json.dumps(index_data))

    slug_dir = tmp_path / "test-playbook"
    slug_dir.mkdir()

    playbook_json = {
        "header": {
            "name": "Test Playbook",
            "purpose": "Monthly metrics for supplier accounts",
            "grain": "monthly, per account",
            "execution_location": "Redshift",
        },
        "objects_referenced": {"tables": ["analytics_bi_viz.core_maker_taker_uuid"]},
        "ctes": [{"cte": "base_data", "purpose": "Filter raw records"}],
    }
    (slug_dir / "test-playbook__playbook.json").write_text(json.dumps(playbook_json))
    (slug_dir / "test-playbook__playbook.md").write_text("# Test Playbook\n\nThis is test documentation.")

    return tmp_path


def test_search_index_finds_matching_entry(playbooks_dir):
    from toolkits.playbook_search import PlaybookSearchTools
    tools = PlaybookSearchTools(playbooks_dir=str(playbooks_dir))
    result = tools.search_index('[["purpose", "monthly metrics"]]')
    parsed = json.loads(result)
    assert len(parsed) >= 1
    assert parsed[0]["slug"] == "test-playbook"
    assert parsed[0]["total_score"] > 0


def test_search_index_no_match(playbooks_dir):
    from toolkits.playbook_search import PlaybookSearchTools
    tools = PlaybookSearchTools(playbooks_dir=str(playbooks_dir))
    result = tools.search_index('[["purpose", "zzz_nonexistent_zzz"]]')
    parsed = json.loads(result)
    assert len(parsed) == 0


def test_search_playbooks_deep(playbooks_dir):
    from toolkits.playbook_search import PlaybookSearchTools
    tools = PlaybookSearchTools(playbooks_dir=str(playbooks_dir))
    result = tools.search_playbooks_deep('[["ctes", "base_data"]]')
    parsed = json.loads(result)
    assert len(parsed) >= 1
    assert parsed[0]["slug"] == "test-playbook"


def test_score_match(playbooks_dir):
    from toolkits.playbook_search import PlaybookSearchTools
    tools = PlaybookSearchTools(playbooks_dir=str(playbooks_dir))
    result = tools.score_match("test-playbook", '[["purpose", "monthly metrics"]]')
    parsed = json.loads(result)
    assert parsed["slug"] == "test-playbook"
    assert parsed["total_score"] > 0


def test_get_playbook_detail(playbooks_dir):
    from toolkits.playbook_search import PlaybookSearchTools
    tools = PlaybookSearchTools(playbooks_dir=str(playbooks_dir))
    result = tools.get_playbook_detail("test-playbook")
    assert "Test Playbook" in result
    assert "test documentation" in result


def test_get_playbook_detail_not_found(playbooks_dir):
    from toolkits.playbook_search import PlaybookSearchTools
    tools = PlaybookSearchTools(playbooks_dir=str(playbooks_dir))
    result = tools.get_playbook_detail("nonexistent-slug")
    assert "not found" in result.lower()
