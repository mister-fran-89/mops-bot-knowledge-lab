# MOPS Knowledge Lab

Unified knowledge assistant for the MOPS team. Combines RAG-powered knowledge retrieval over MOPS docs and SQL playbooks with SQL execution against Redshift.

## Stack

| Component | Detail |
|-----------|--------|
| Framework | [Agno](https://github.com/agno-agi/agno) 2.5+ |
| LLM | Claude via AWS Bedrock |
| API | FastAPI on `:7777` (`agents.py`) |
| UI | Next.js on `:3000` (`ui/`) |
| Embedder | `nomic-embed-text` via Ollama (768 dim) |
| Vector DB | LanceDB (local file) |
| Session DB | SQLite (`data/mops.db`) |

## Agents

| Agent | Purpose | Tools |
|-------|---------|-------|
| **MOPS Assistant** | General knowledge hub, orchestrator | PlaybookSearch, SQLExecution |
| **SQL Archivist** | Read-only playbook retrieval, duplicate detection | PlaybookSearch, SQLComparison |
| **SQL Executor** | Run SQL against Redshift, export CSV | SQLExecution |
| **SQL Librarian** | Transform raw SQL into structured playbook entries | PlaybookWrite, PlaybookSearch, SQLComparison |

## Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Copy and configure env
cp .env.example .env
# Edit .env — set AWS credentials, Redshift credentials, Ollama host

# 3. Index knowledge base
mkdir -p knowledge data
# Place .md/.txt files in knowledge/ for general MOPS docs
python reindex.py          # incremental
python reindex.py --fresh  # full rebuild

# 4. Start API
python agents.py
# → http://localhost:7777

# 5. Start UI (separate terminal)
cd ui
pnpm install
pnpm dev
# → http://localhost:3000
```

## Environment Variables

See `.env.example` for all variables. Key ones:

```env
# AWS Bedrock (required)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Embedder (required for RAG)
OLLAMA_HOST=http://localhost:11434

# Redshift (required for SQL Executor)
REDSHIFT_HOST=redshift.atlas.c2fo.io
REDSHIFT_PORT=5439
REDSHIFT_DB=atlas
REDSHIFT_USER=
REDSHIFT_PASSWORD=

# Paths
PLAYBOOKS_DIR=../engines/sql-librarian-engine-v1/playbooks
LIBRARIAN_ENGINE_DIR=../engines/sql-librarian-engine-v1
```

## Knowledge Indexing

The `reindex.py` script indexes two sources into the RAG vector store:

1. **Playbook corpus** — `playbook.md`, `playbook.json`, `documented.sql` per slug from the SQL Librarian Engine
2. **General knowledge** — `.md` and `.txt` files in `knowledge/`

```bash
python reindex.py          # incremental (skip existing)
python reindex.py --fresh  # wipe and rebuild
```

## Tests

```bash
cd mops-bot-knowledge-lab
python -m pytest tests/ -v
```
