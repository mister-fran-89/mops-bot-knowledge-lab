import os
import json
import dataclasses
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv("/opt/agno/.env")

from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.vectordb.lancedb.lance_db import LanceDb
from agno.db.sqlite import SqliteDb
from agno.db.base import SessionType
from agno.memory.manager import MemoryManager

# ── Config ─────────────────────────────────────────────────────────────────────
_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.1.246:11434")
_ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
_DB_ID = "local"

# ── Persistent DB (sessions + memories) ───────────────────────────────────────
_db = SqliteDb(db_file="/opt/agno/data/agno.db")

# ── Knowledge base (RAG — LanceDB + nomic-embed-text) ─────────────────────────
_embedder = OllamaEmbedder(
    id="nomic-embed-text",
    host=_OLLAMA_HOST,
    dimensions=768,
)
_vdb = LanceDb(
    uri="/opt/agno/lancedb",
    table_name="franlab_knowledge",
    embedder=_embedder,
)
_knowledge = Knowledge(vector_db=_vdb, max_results=20)

_INSTRUCTIONS = [
    "The user's name is Fran.",
    "Fran lives in Weston-super-Mare, UK.",
    "Fran runs a Proxmox home server at 192.168.1.150 called 'fran'.",
    "All FranLab services are on the 192.168.1.x LAN and accessible via *.franlab.uk subdomains.",
    "When asked about a service, URL, or anything lab-related, search your knowledge base first.",
    "You have persistent memory — remember facts Fran tells you across conversations.",
    "Be concise and direct.",
    "When you store a memory, you MUST call the memory tool first. Only confirm it is saved AFTER the tool call succeeds. Never say you have saved something unless the tool call has already completed.",
    "If you cannot save a memory (tool unavailable or failed), say so honestly. Do not pretend to save.",
]

# ── Agents ─────────────────────────────────────────────────────────────────────
_agents: dict[str, Agent] = {}

_qwen_memory = MemoryManager(
    model=Ollama(id="qwen2.5:7b-instruct-q4_K_M", host=_OLLAMA_HOST),
    db=_db,
)

_agents["qwen-7b"] = Agent(
    id="qwen-7b",
    name="Qwen 7B (Local)",
    model=Ollama(id="qwen2.5:7b-instruct-q4_K_M", host=_OLLAMA_HOST),
    description="Local Qwen 2.5 7B via Ollama on Mac Mini.",
    instructions=_INSTRUCTIONS,
    knowledge=_knowledge,
    search_knowledge=True,
    db=_db,
    user_id="fran",
    memory_manager=_qwen_memory,
    enable_agentic_memory=True,
    update_memory_on_run=True,
    enable_user_memories=True,
    add_history_to_context=True,
    markdown=True,
)

_agents["phi4-mini"] = Agent(
    id="phi4-mini",
    name="Phi4 Mini (Fast)",
    model=Ollama(id="phi4-mini:3.8b", host=_OLLAMA_HOST),
    description="Fast local Phi4 Mini via Ollama — best for quick casual queries.",
    instructions=_INSTRUCTIONS,
    db=_db,
    user_id="fran",
    add_history_to_context=True,
    markdown=True,
)

if _ANTHROPIC_KEY and _ANTHROPIC_KEY != "your-key-here":
    from agno.models.anthropic import Claude
    _claude_memory = MemoryManager(
        model=Claude(id="claude-sonnet-4-6"),
        db=_db,
    )
    _agents["claude-sonnet"] = Agent(
        id="claude-sonnet",
        name="Claude Sonnet 4.6",
        model=Claude(id="claude-sonnet-4-6"),
        description="Anthropic Claude Sonnet 4.6.",
        instructions=_INSTRUCTIONS,
        knowledge=_knowledge,
        search_knowledge=True,
        db=_db,
        user_id="fran",
        memory_manager=_claude_memory,
        enable_agentic_memory=True,
        update_memory_on_run=True,
        enable_user_memories=True,
        add_history_to_context=True,
            markdown=True,
    )

# ── Serialiser ─────────────────────────────────────────────────────────────────
def _safe_json(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _safe_json(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Agno Playground")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "available"}

@app.get("/agents")
def get_agents():
    return [
        {"id": a.id, "name": a.name, "description": a.description, "db_id": _DB_ID}
        for a in _agents.values()
    ]

@app.get("/teams")
def get_teams():
    return []

@app.get("/sessions")
def get_sessions(
    type: str = Query("agent"),
    component_id: str = Query(...),
    db_id: str = Query(None),
    limit: int = Query(50),
    page: int = Query(1),
):
    try:
        session_type = SessionType.AGENT if type == "agent" else SessionType.TEAM
        sessions = _db.get_sessions(
            session_type=session_type,
            component_id=component_id,
            user_id="fran",
            limit=limit,
            page=page,
            deserialize=False,
        )
        if isinstance(sessions, tuple):
            data, total = sessions
        else:
            data = [_safe_json(s) for s in sessions]
            total = len(data)
        return {"data": data, "meta": {"total": total, "page": page, "limit": limit}}
    except Exception as e:
        return {"data": [], "meta": {"total": 0, "page": 1, "limit": limit}}

@app.get("/sessions/{session_id}/runs")
def get_session_runs(
    session_id: str,
    type: str = Query("agent"),
    db_id: str = Query(None),
):
    try:
        session_type = SessionType.AGENT if type == "agent" else SessionType.TEAM
        session = _db.get_session(
            session_id=session_id,
            session_type=session_type,
            user_id="fran",
            deserialize=False,
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        runs = session.get("runs", []) if isinstance(session, dict) else []
        return _safe_json(runs)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db_id: str = Query(None),
):
    try:
        _db.delete_session(session_id=session_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/{agent_id}/runs")
async def agent_run(
    agent_id: str,
    message: str = Form(...),
    stream: Optional[str] = Form("true"),
    session_id: Optional[str] = Form(None),
):
    agent = _agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    sid = session_id if session_id else None

    def _stream():
        try:
            for event in agent.run(
                message,
                stream=True,
                stream_events=True,
                session_id=sid,
            ):
                payload = _safe_json(event)
                yield f"data: {json.dumps(payload)}\n\n"
        except Exception as exc:
            err = {"event": "RunError", "content": str(exc)}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agents:app", host="0.0.0.0", port=7777, reload=False)
