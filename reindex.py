#!/usr/bin/env python3
"""
Index MOPS knowledge into the RAG vector store.

Sources:
  1. Playbook corpus — playbook.md, playbook.json, documented.sql per slug
  2. General knowledge — .md and .txt files in knowledge/

Usage:
  python reindex.py          # incremental (skip existing)
  python reindex.py --fresh  # wipe and rebuild from scratch
"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.vectordb.lancedb.lance_db import LanceDb
from agno.knowledge.knowledge import Knowledge

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LANCEDB_URI = os.getenv("LANCEDB_URI", "./data/lancedb")
PLAYBOOKS_DIR = Path(os.getenv("PLAYBOOKS_DIR", "../engines/sql-librarian-engine-v1/playbooks"))
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", "./knowledge"))
TABLE_NAME = "mops_knowledge"

fresh = "--fresh" in sys.argv

embedder = OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_HOST, dimensions=768)
vdb = LanceDb(uri=LANCEDB_URI, table_name=TABLE_NAME, embedder=embedder)
knowledge = Knowledge(vector_db=vdb)

count = 0

# ── Index playbook corpus ────────────────────────────────────────────────────
if PLAYBOOKS_DIR.is_dir():
    for slug_dir in sorted(PLAYBOOKS_DIR.iterdir()):
        if not slug_dir.is_dir() or slug_dir.name == "__pycache__":
            continue
        slug = slug_dir.name
        artifacts = [
            (f"{slug}__playbook.md", f"{slug}/playbook-md"),
            (f"{slug}__playbook.json", f"{slug}/playbook-json"),
            (f"{slug}__documented.sql", f"{slug}/documented-sql"),
        ]
        for filename, doc_name in artifacts:
            filepath = slug_dir / filename
            if filepath.is_file():
                print(f"  Indexing playbook: {slug}/{filename}")
                # For JSON files, flatten to readable text
                if filename.endswith(".json"):
                    with open(filepath, encoding="utf-8") as f:
                        data = json.load(f)
                    content = json.dumps(data, indent=2)
                    # Write temp text file for indexing
                    tmp = slug_dir / f"{slug}__playbook_text.txt"
                    tmp.write_text(content, encoding="utf-8")
                    knowledge.insert(path=str(tmp), name=doc_name, upsert=True, skip_if_exists=not fresh)
                    tmp.unlink()
                else:
                    knowledge.insert(path=str(filepath), name=doc_name, upsert=True, skip_if_exists=not fresh)
                count += 1
    print(f"Indexed {count} playbook artifacts.")
else:
    print(f"Playbooks directory not found: {PLAYBOOKS_DIR}")

# ── Index general knowledge ──────────────────────────────────────────────────
gen_count = 0
if KNOWLEDGE_DIR.is_dir():
    files = list(KNOWLEDGE_DIR.glob("*.md")) + list(KNOWLEDGE_DIR.glob("*.txt"))
    print(f"Found {len(files)} knowledge files in {KNOWLEDGE_DIR}")
    for f in files:
        print(f"  Indexing knowledge: {f.name}")
        knowledge.insert(path=str(f), name=f.stem, upsert=True, skip_if_exists=not fresh)
        gen_count += 1
    print(f"Indexed {gen_count} knowledge files.")
else:
    print(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

print(f"Done. Total: {count + gen_count} documents indexed.")
