import json
import pytest
from pathlib import Path


@pytest.fixture
def engine_dir(tmp_path):
    """Create a minimal librarian engine structure."""
    playbooks_dir = tmp_path / "playbooks"
    playbooks_dir.mkdir()

    index_data = {
        "engine_name": "SQL Librarian Engine",
        "engine_version": "v1",
        "last_updated": "2026-04-17",
        "total_entries": 0,
        "entries": [],
    }
    (playbooks_dir / "INDEX.json").write_text(json.dumps(index_data))

    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    schema = {
        "type": "object",
        "required": ["header"],
        "properties": {
            "header": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            }
        },
    }
    (schemas_dir / "playbook-schema.json").write_text(json.dumps(schema))

    return tmp_path


def test_create_playbook_folder(engine_dir):
    from toolkits.playbook_write import PlaybookWriteTools
    tools = PlaybookWriteTools(
        engine_dir=str(engine_dir),
        playbooks_dir=str(engine_dir / "playbooks"),
    )
    result = tools.create_playbook_folder("new-playbook")
    assert "created" in result.lower()
    assert (engine_dir / "playbooks" / "new-playbook").is_dir()


def test_create_playbook_folder_already_exists(engine_dir):
    from toolkits.playbook_write import PlaybookWriteTools
    tools = PlaybookWriteTools(
        engine_dir=str(engine_dir),
        playbooks_dir=str(engine_dir / "playbooks"),
    )
    (engine_dir / "playbooks" / "existing").mkdir()
    result = tools.create_playbook_folder("existing")
    assert "already exists" in result.lower()


def test_write_artifact(engine_dir):
    from toolkits.playbook_write import PlaybookWriteTools
    tools = PlaybookWriteTools(
        engine_dir=str(engine_dir),
        playbooks_dir=str(engine_dir / "playbooks"),
    )
    (engine_dir / "playbooks" / "test-slug").mkdir()
    result = tools.write_artifact("test-slug", "raw.sql", "SELECT 1;")
    assert "written" in result.lower()
    written = (engine_dir / "playbooks" / "test-slug" / "test-slug__raw.sql").read_text()
    assert written == "SELECT 1;"


def test_write_artifact_invalid_name(engine_dir):
    from toolkits.playbook_write import PlaybookWriteTools
    tools = PlaybookWriteTools(
        engine_dir=str(engine_dir),
        playbooks_dir=str(engine_dir / "playbooks"),
    )
    (engine_dir / "playbooks" / "test-slug").mkdir()
    result = tools.write_artifact("test-slug", "evil.sh", "rm -rf /")
    assert "error" in result.lower() or "invalid" in result.lower()


def test_write_artifact_validates_playbook_json(engine_dir):
    from toolkits.playbook_write import PlaybookWriteTools
    tools = PlaybookWriteTools(
        engine_dir=str(engine_dir),
        playbooks_dir=str(engine_dir / "playbooks"),
    )
    (engine_dir / "playbooks" / "test-slug").mkdir()
    # Invalid: missing required header.name
    result = tools.write_artifact("test-slug", "playbook.json", '{"header": {}}')
    assert "error" in result.lower() or "validation" in result.lower()


def test_update_index(engine_dir):
    from toolkits.playbook_write import PlaybookWriteTools
    tools = PlaybookWriteTools(
        engine_dir=str(engine_dir),
        playbooks_dir=str(engine_dir / "playbooks"),
    )
    metadata = json.dumps({
        "slug": "new-playbook",
        "name": "New Playbook",
        "purpose": "Test purpose",
        "status": "draft",
        "execution_location": "Redshift",
        "tables": [],
    })
    result = tools.update_index("new-playbook", metadata)
    assert "updated" in result.lower()

    with open(engine_dir / "playbooks" / "INDEX.json") as f:
        index = json.load(f)
    assert index["total_entries"] == 1
    assert index["entries"][0]["slug"] == "new-playbook"
