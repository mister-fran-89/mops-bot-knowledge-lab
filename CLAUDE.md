# MOPS Knowledge Lab

Multi-agent AI knowledge system for the MOPS (Market Operations Specialist) team at C2FO.

## Architecture

- **Backend:** FastAPI (`agents.py`) on port 7777, using Agno 2.5+ framework
- **Frontend:** Next.js 15 (`ui/`) on port 3000, React 18, TypeScript, Tailwind CSS
- **LLM:** Claude Opus 4.7 via AWS Bedrock (application inference profile)
- **Memory extraction:** Claude Haiku 4.5 via Bedrock (fast, cheap fact extraction)
- **Session/memory DB:** SQLite at `./data/mops.db` (tables: `agno_sessions`, `agno_memories`)
- **Knowledge search:** Keyword-based file search over `./knowledge/` directory (no vector DB needed)
- **Playbook corpus:** External dependency at `../engines/sql-librarian-engine-v1/playbooks/`

## Agents

| Agent | ID | Purpose | Tools |
|-------|-----|---------|-------|
| MOPS Assistant | `mops-assistant` | Orchestrator — knowledge hub, memory, search | PlaybookSearch, SQLExecution, KnowledgeSearch |
| SQL Archivist | `sql-archivist` | Read-only playbook retrieval | PlaybookSearch, SQLComparison |
| SQL Executor | `sql-executor` | Run SQL against Redshift | SQLExecution |
| SQL Librarian | `sql-librarian` | Document raw SQL into playbooks | PlaybookWrite, PlaybookSearch, SQLComparison |

Only the MOPS Assistant has persistent memory (`update_memory_on_run=True`). Other agents are stateless.

## Key Files

- `agents.py` — Backend entry point: all agents, API routes, model config
- `toolkits/` — Agent tools: playbook_search, sql_execution, sql_comparison, playbook_write, knowledge_search
- `knowledge/` — Plain text/markdown knowledge files, searched by keyword (no indexing needed)
- `reindex.py` — Legacy RAG indexer (LanceDB + Ollama). Kept for potential future use but not currently active
- `ui/src/components/chat/` — Chat UI components
- `ui/src/hooks/useAIStreamHandler.tsx` — SSE event handler for agent responses
- `ui/src/store.ts` — Zustand state store

## Models

- **Main model:** Bedrock inference profile ARN (Opus 4.7) — set via `BEDROCK_MODEL_ID` env var
- **Memory model:** Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) — used by MemoryManager for fast fact extraction
- **Guardrails:** Optional PII guardrail via `BEDROCK_GUARDRAIL_ID` / `BEDROCK_GUARDRAIL_VERSION`. Note: this guardrail strips personal information from responses, which can cause the agent to omit knowledge file content containing names, dates, or family info

## Knowledge System

Knowledge files live in `./knowledge/` and subfolders. Supported formats: `.txt`, `.md`, `.yaml`, `.yml`, `.json`. Files are read from disk on every search — no indexing step, no external dependencies.

The `KnowledgeSearchTools` toolkit provides:
- `search_knowledge(query)` — keyword search with stop-word filtering; falls back to returning all files if no keywords match
- `list_knowledge_files()` — lists all available knowledge files

To add knowledge: drop a file in `knowledge/`. It's immediately searchable.

## Memory System

Agent memory is stored in SQLite (`agno_memories` table). The Haiku model extracts facts after each MOPS Assistant conversation.

Inspect memory: `python -c "import sqlite3; [print(r[1]) for r in sqlite3.connect('./data/mops.db').execute('SELECT memory_id, memory FROM agno_memories')]"`

Clear memory: `python -c "import sqlite3; c=sqlite3.connect('./data/mops.db'); c.execute('DELETE FROM agno_memories'); c.commit()"`

Memory can hallucinate or store incorrect facts. Knowledge files are the source of truth.

## Streaming

The `/agents/{agent_id}/runs` endpoint uses async streaming (`agent.arun()` with `async for`). Events are SSE-formatted JSON. The frontend handles `MemoryUpdateStarted` and `MemoryUpdateCompleted` events to show a "Remembering..." / "Memory saved" indicator.

## Frontend

- Custom `ChatBlankState` shows selected agent name/description (not Agno branding)
- Code blocks have copy button and language label (`CodeBlock` in `styles.tsx`)
- `@tailwindcss/typography` installed for prose rendering
- Heading sizes tightened for chat context (h1: 18px, h2: 16px, h3+: 14px)
- Tables use full container width

## Running

```bash
# Backend
python -m uvicorn agents:app --host 0.0.0.0 --port 7777 --reload

# Frontend
cd ui && npm run dev
```

## External Dependencies

- **Playbook corpus:** Requires `../engines/sql-librarian-engine-v1/` sibling directory
- **AWS Bedrock:** Requires valid AWS credentials with access to Claude models
- **Redshift:** Required for SQL Executor agent (connection via env vars)
- **Ollama:** Only needed if using the legacy RAG pipeline (`reindex.py`). Not needed for current keyword-based knowledge search

## Environment Variables

See `.env.example` for full list. Key vars:
- `BEDROCK_MODEL_ID` — Main LLM (default: Opus 4.7 inference profile ARN)
- `BEDROCK_HAIKU_MODEL_ID` — Memory extraction model
- `BEDROCK_GUARDRAIL_ID` / `BEDROCK_GUARDRAIL_VERSION` — Optional PII guardrail
- `PLAYBOOKS_DIR` — Path to playbook corpus
- `KNOWLEDGE_DIR` — Path to knowledge files (default: `./knowledge`)
- `REDSHIFT_*` — Redshift connection settings
