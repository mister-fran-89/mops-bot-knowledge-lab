import re
from pathlib import Path
from agno.tools import Toolkit


class KnowledgeSearchTools(Toolkit):

    def __init__(self, knowledge_dir: str = "./knowledge"):
        super().__init__(name="KnowledgeSearchTools")
        self.knowledge_dir = Path(knowledge_dir)
        self.register(self.search_knowledge)
        self.register(self.list_knowledge_files)

    def _load_files(self) -> list[dict]:
        results = []
        if not self.knowledge_dir.is_dir():
            return results
        for f in sorted(self.knowledge_dir.rglob("*")):
            if f.is_file() and f.suffix in (".txt", ".md", ".yaml", ".yml", ".json"):
                try:
                    content = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                rel = f.relative_to(self.knowledge_dir)
                results.append({"path": str(rel), "content": content})
        return results

    def search_knowledge(self, query: str) -> str:
        """Search all knowledge files by keyword (case-insensitive).
        Returns matching files ranked by relevance. If no keyword matches, returns ALL files.
        IMPORTANT: Search for the actual topic (e.g. 'fran', 'team', 'yield'), NOT meta-words like 'knowledge base' or 'search'."""
        tokens = set(re.split(r"\s+", query.lower().strip()))
        tokens -= {"who", "what", "where", "when", "how", "why", "is", "are", "was",
                    "the", "a", "an", "do", "does", "did", "about", "know", "tell",
                    "me", "you", "can", "search", "find", "look", "up", "for", "in",
                    "knowledge", "base", "file", "files", "folder", "information"}
        tokens.discard("")

        files = self._load_files()
        if not files:
            return "No knowledge files found."

        if not tokens:
            parts = []
            for f in files:
                parts.append(f"### {f['path']}\n{f['content'].strip()}")
            return f"Returning all {len(files)} knowledge files:\n\n" + "\n\n---\n\n".join(parts)

        matches = []
        for f in files:
            content_lower = f["content"].lower()
            matched_tokens = {t for t in tokens if t in content_lower}
            if matched_tokens:
                score = len(matched_tokens) / len(tokens)
                matches.append({"path": f["path"], "content": f["content"], "score": score})

        matches.sort(key=lambda m: m["score"], reverse=True)

        if not matches:
            parts = []
            for f in files:
                parts.append(f"### {f['path']}\n{f['content'].strip()}")
            return f"No keyword matches for '{query}'. Returning all {len(files)} files:\n\n" + "\n\n---\n\n".join(parts)

        parts = []
        for m in matches[:10]:
            parts.append(f"### {m['path']} (score: {m['score']:.0%})\n{m['content'].strip()}")
        return "\n\n---\n\n".join(parts)

    def list_knowledge_files(self) -> str:
        """List all knowledge files available for search, including files in subfolders."""
        files = self._load_files()
        if not files:
            return "No knowledge files found."
        lines = [f"- {f['path']} ({len(f['content'])} chars)" for f in files]
        return f"Found {len(files)} knowledge files:\n" + "\n".join(lines)
