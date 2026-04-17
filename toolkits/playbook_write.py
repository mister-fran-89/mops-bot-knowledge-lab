"""PlaybookWriteTools — Create and write playbook artifacts.

Used exclusively by the SQL Librarian agent to transform raw SQL
into structured playbook entries following the v1 contract.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from agno.tools import Toolkit

_VALID_ARTIFACTS = {
    "raw.sql",
    "documented.sql",
    "playbook.md",
    "playbook.json",
    "answers.yaml",
}


class PlaybookWriteTools(Toolkit):
    def __init__(self, engine_dir: str, playbooks_dir: str):
        self.engine_dir = engine_dir
        self.playbooks_dir = playbooks_dir
        tools = [
            self.create_playbook_folder,
            self.write_artifact,
            self.update_index,
        ]
        super().__init__(name="playbook_write", tools=tools)

    def create_playbook_folder(self, slug: str) -> str:
        """Create a new playbook folder.

        Args:
            slug: The playbook slug (kebab-case identifier).
        """
        folder = Path(self.playbooks_dir) / slug
        if folder.exists():
            return f"Folder already exists: {folder}"
        folder.mkdir(parents=True)
        return f"Created playbook folder: {folder}"

    def write_artifact(self, slug: str, artifact: str, content: str) -> str:
        """Write a playbook artifact file.

        Args:
            slug: The playbook slug.
            artifact: Artifact name — one of: raw.sql, documented.sql, playbook.md, playbook.json, answers.yaml
            content: The file content to write.
        """
        if artifact not in _VALID_ARTIFACTS:
            return f"**Error:** Invalid artifact name '{artifact}'. Must be one of: {', '.join(sorted(_VALID_ARTIFACTS))}"

        folder = Path(self.playbooks_dir) / slug
        if not folder.is_dir():
            return f"**Error:** Playbook folder does not exist: {folder}. Call create_playbook_folder first."

        # Validate playbook.json against schema before writing
        if artifact == "playbook.json":
            schema_path = Path(self.engine_dir) / "schemas" / "playbook-schema.json"
            if schema_path.is_file():
                try:
                    import jsonschema
                    with open(schema_path, encoding="utf-8") as f:
                        schema = json.load(f)
                    data = json.loads(content)
                    jsonschema.validate(data, schema)
                except jsonschema.ValidationError as e:
                    return f"**Error:** Schema validation failed: {e.message}"
                except json.JSONDecodeError as e:
                    return f"**Error:** Invalid JSON: {e}"

        file_path = folder / f"{slug}__{artifact}"
        file_path.write_text(content, encoding="utf-8")
        return f"Written: {file_path}"

    def update_index(self, slug: str, metadata: str) -> str:
        """Add or update a playbook entry in INDEX.json.

        Args:
            slug: The playbook slug.
            metadata: JSON string with entry fields: name, purpose, status, execution_location, tables, etc.
        """
        index_path = Path(self.playbooks_dir) / "INDEX.json"
        if not index_path.is_file():
            return "**Error:** INDEX.json not found"

        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)

        entry_data = json.loads(metadata)
        entry_data["slug"] = slug
        entry_data["path"] = f"playbooks/{slug}"
        entry_data["files"] = {
            "raw": f"{slug}__raw.sql",
            "documented": f"{slug}__documented.sql",
            "playbook_md": f"{slug}__playbook.md",
            "playbook_json": f"{slug}__playbook.json",
            "answers": f"{slug}__answers.yaml",
        }

        entries = index.get("entries", [])
        existing_idx = next((i for i, e in enumerate(entries) if e.get("slug") == slug), None)
        if existing_idx is not None:
            entries[existing_idx] = entry_data
        else:
            entries.append(entry_data)

        index["entries"] = entries
        index["total_entries"] = len(entries)
        index["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

        return f"INDEX.json updated — {slug} ({'updated' if existing_idx is not None else 'added'}), {len(entries)} total entries"
