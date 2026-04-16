# FranLab Agno — Personal AI Agent

Personal AI assistant running on LXC 114 (192.168.1.61) in the FranLab Proxmox home server.

## Stack

| Component | Detail |
|-----------|--------|
| Framework | [Agno](https://github.com/agno-agi/agno) 2.5.17 |
| API | FastAPI on `:7777` (`agents.py`) |
| UI | Next.js `agent-ui` on `:3000` (`/opt/agno-ui/`) |
| Models | Qwen 2.5 7B + Phi4 Mini 3.8B via Ollama (Mac Mini 192.168.1.246) |
| Embedder | `nomic-embed-text` via Ollama (768 dim) |
| Vector DB | LanceDB (local file) |
| Memory DB | SQLite (`data/agno.db`) — sessions + user memories |

## Agents

- **qwen-7b** — full toolset: RAG search, user memory, session persistence
- **phi4-mini** — fast casual chat, no tools (model too small for reliable tool use)

## Setup

```bash
# 1. Create venv and install deps
python3 -m venv venv
source venv/bin/activate
pip install agno fastapi uvicorn python-dotenv lancedb tantivy sqlalchemy aiosqlite

# 2. Copy env file
cp .env.example .env
# Edit .env — set OLLAMA_HOST and optionally ANTHROPIC_API_KEY

# 3. Index knowledge base
mkdir -p knowledge lancedb data
# Drop .md files into knowledge/
python3 reindex.py

# 4. Start API
python3 agents.py

# 5. Start UI (separate terminal)
cd /opt/agno-ui
pnpm install
pnpm build
pnpm start
```

## Knowledge Base

Drop `.md` or `.txt` files into `knowledge/` then re-index:

```bash
python3 reindex.py          # incremental
python3 reindex.py --fresh  # full rebuild
```

## Services (systemd)

```
agno-api.service  — FastAPI API on :7777
agno-ui.service   — Next.js UI on :3000
```

## Environment Variables

```env
OLLAMA_HOST=http://192.168.1.246:11434
ANTHROPIC_API_KEY=          # optional — enables Claude Sonnet agent
```
