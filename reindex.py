#!/opt/agno/venv/bin/python3
"""
Run this script to index/reindex all files in /opt/agno/knowledge/ into the RAG vector store.
Usage:
  python3 reindex.py          # incremental (skip existing)
  python3 reindex.py --fresh  # wipe and rebuild from scratch
"""
import sys
from pathlib import Path
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.vectordb.lancedb.lance_db import LanceDb
from agno.knowledge.knowledge import Knowledge

OLLAMA_HOST = "http://192.168.1.246:11434"
KNOWLEDGE_DIR = Path("/opt/agno/knowledge")
LANCEDB_URI = "/opt/agno/lancedb"
TABLE_NAME = "franlab_knowledge"

fresh = "--fresh" in sys.argv

embedder = OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_HOST, dimensions=768)
vdb = LanceDb(uri=LANCEDB_URI, table_name=TABLE_NAME, embedder=embedder)
knowledge = Knowledge(vector_db=vdb)

files = list(KNOWLEDGE_DIR.glob("*.md")) + list(KNOWLEDGE_DIR.glob("*.txt"))
print(f"Found {len(files)} files in {KNOWLEDGE_DIR}")

for f in files:
    print(f"  Indexing {f.name}...")
    knowledge.insert(
        path=str(f),
        name=f.stem,
        upsert=True,
        skip_if_exists=not fresh,
    )

print("Done.")
