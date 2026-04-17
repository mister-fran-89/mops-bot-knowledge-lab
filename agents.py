# agents.py — MOPS Knowledge Lab backend
import os
import json
import dataclasses
from typing import Optional, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agno.agent import Agent
from agno.models.aws import Claude
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.vectordb.lancedb.lance_db import LanceDb
from agno.db.sqlite import SqliteDb
from agno.db.base import SessionType
from agno.memory.manager import MemoryManager

from toolkits import PlaybookSearchTools, SQLExecutionTools, SQLComparisonTools, PlaybookWriteTools

# ── Config ─────────────────────────────────────────────────────────────────────
_BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
_AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
_BEDROCK_GUARDRAIL_ID = os.getenv("BEDROCK_GUARDRAIL_ID", "")
_BEDROCK_GUARDRAIL_VERSION = os.getenv("BEDROCK_GUARDRAIL_VERSION", "")
_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_USER_ID = os.getenv("USER_ID", "mops")

_SQLITE_DB = os.getenv("SQLITE_DB", "./data/mops.db")
_LANCEDB_URI = os.getenv("LANCEDB_URI", "./data/lancedb")
_PLAYBOOKS_DIR = os.getenv("PLAYBOOKS_DIR", "../engines/sql-librarian-engine-v1/playbooks")
_LIBRARIAN_ENGINE_DIR = os.getenv("LIBRARIAN_ENGINE_DIR", "../engines/sql-librarian-engine-v1")
_KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "./knowledge")
_RESULTS_DIR = os.getenv("RESULTS_DIR", "./data/results")
_DB_ID = "local"

# Ensure data directory exists
Path(_SQLITE_DB).parent.mkdir(parents=True, exist_ok=True)

# ── Model ────────────────────────────────────────────────────────────────────
_model_kwargs: dict[str, Any] = {"id": _BEDROCK_MODEL_ID, "aws_region": _AWS_REGION}
if _BEDROCK_GUARDRAIL_ID:
    _model_kwargs["request_params"] = {
        "extra_headers": {
            "X-Amzn-Bedrock-GuardrailIdentifier": _BEDROCK_GUARDRAIL_ID,
            "X-Amzn-Bedrock-GuardrailVersion": _BEDROCK_GUARDRAIL_VERSION or "1",
        }
    }
_model = Claude(**_model_kwargs)

# ── Persistent DB (sessions + memories) ───────────────────────────────────────
_db = SqliteDb(db_file=_SQLITE_DB)

# ── Knowledge base (RAG — LanceDB + nomic-embed-text) ─────────────────────────
_embedder = OllamaEmbedder(
    id="nomic-embed-text",
    host=_OLLAMA_HOST,
    dimensions=768,
)
_vdb = LanceDb(
    uri=_LANCEDB_URI,
    table_name="mops_knowledge",
    embedder=_embedder,
)
_knowledge = Knowledge(vector_db=_vdb, max_results=20)

# ── Toolkits ──────────────────────────────────────────────────────────────────
_search_tools = PlaybookSearchTools(playbooks_dir=_PLAYBOOKS_DIR)
_exec_tools = SQLExecutionTools(playbooks_dir=_PLAYBOOKS_DIR, results_dir=_RESULTS_DIR)
_compare_tools = SQLComparisonTools(playbooks_dir=_PLAYBOOKS_DIR)
_write_tools = PlaybookWriteTools(engine_dir=_LIBRARIAN_ENGINE_DIR, playbooks_dir=_PLAYBOOKS_DIR)

# ── Memory manager ────────────────────────────────────────────────────────────
_memory_manager = MemoryManager(model=_model, db=_db)

# ── Agent instructions ────────────────────────────────────────────────────────
_ORCHESTRATOR_INSTRUCTIONS = [
    "You are the MOPS Assistant — a knowledge hub for the MOPS team.",
    "Search your knowledge base first when answering questions about MOPS processes, playbooks, or domain topics.",
    "For playbook lookups, use PlaybookSearchTools: search_index for fast lookup, search_playbooks_deep for detailed field search.",
    "For SQL execution, use SQLExecutionTools: list_playbooks to help users find scripts, run_query or run_playbook to execute.",
    "Be concise and direct. Present data as tables when appropriate.",
    "You have persistent memory — remember facts users tell you across conversations.",
]

_ARCHIVIST_INSTRUCTIONS = [
    "You are the SQL Archivist — a read-only retrieval engine for the SQL playbook corpus.",
    "You decode structured playbook artifacts into answers.",
    "Before searching, decompose every query into librarian encoding fields: business_question, grain, inputs, outputs, execution_location, purpose, filters, time_window, objects_referenced, ctes.",
    "Use search_index first (fast). Only use search_playbooks_deep when index results are insufficient.",
    "Use compare_sql when checking for duplicate scripts.",
    "You NEVER modify any file. Read-only. Absolute. No exceptions.",
    "Maximum 5 results for direct search, 3 for script lookup, all above 0.5 for duplicate check.",
]

_EXECUTOR_INSTRUCTIONS = [
    "You are the SQL Executor — you run SQL against Redshift and present results.",
    "Use list_playbooks to help users find the right script.",
    "Use run_playbook when the user names a specific slug, run_query for raw SQL.",
    "Use export_csv when the user needs full results downloaded.",
    "Only SELECT and WITH queries are allowed. Never construct database connections yourself.",
    "Present results as markdown tables. Be concise.",
]

_LIBRARIAN_INSTRUCTIONS = [
    "You are the SQL Librarian Engine — you transform raw SQL scripts into structured playbook entries.",
    "Given a SQL script, produce 5 artifacts: raw.sql, documented.sql, playbook.md, playbook.json, answers.yaml.",
    "Use compare_sql first to check for duplicates before documenting.",
    "Use create_playbook_folder, write_artifact, and update_index to create entries.",
    "Follow the v1 contract: maximum 3 questions per run, never re-ask resolved questions.",
    "Preserve SQL logic exactly in documented.sql — no expression changes.",
    "Generate ALL SQL PLAYBOOK HEADER v1 fields; mark unknown values explicitly.",
    "If execution_location is unclear, ask. If unanswered, set status to 'blocked'.",
    "Validate playbook.json against the schema before writing.",
    "Update INDEX.json after every change.",
]

# ── Agents ─────────────────────────────────────────────────────────────────────
_agents: dict[str, Agent] = {}

_agents["mops-assistant"] = Agent(
    id="mops-assistant",
    name="MOPS Assistant",
    model=_model,
    description="MOPS team knowledge assistant — ask about processes, playbooks, run SQL, search docs.",
    instructions=_ORCHESTRATOR_INSTRUCTIONS,
    knowledge=_knowledge,
    search_knowledge=True,
    tools=[_search_tools, _exec_tools],
    db=_db,
    user_id=_USER_ID,
    memory_manager=_memory_manager,
    enable_agentic_memory=True,
    update_memory_on_run=True,
    enable_user_memories=True,
    add_history_to_context=True,
    markdown=True,
)

_agents["sql-archivist"] = Agent(
    id="sql-archivist",
    name="SQL Archivist",
    model=_model,
    description="Search and retrieve SQL playbooks — handles business questions, duplicate detection, script lookups.",
    instructions=_ARCHIVIST_INSTRUCTIONS,
    tools=[_search_tools, _compare_tools],
    db=_db,
    user_id=_USER_ID,
    add_history_to_context=True,
    markdown=True,
)

_agents["sql-executor"] = Agent(
    id="sql-executor",
    name="SQL Executor",
    model=_model,
    description="Run SQL against Redshift — execute playbook scripts or raw queries, export to CSV.",
    instructions=_EXECUTOR_INSTRUCTIONS,
    tools=[_exec_tools],
    db=_db,
    user_id=_USER_ID,
    add_history_to_context=True,
    markdown=True,
)

_agents["sql-librarian"] = Agent(
    id="sql-librarian",
    name="SQL Librarian",
    model=_model,
    description="Transform raw SQL scripts into structured playbook documentation.",
    instructions=_LIBRARIAN_INSTRUCTIONS,
    tools=[_write_tools, _search_tools, _compare_tools],
    db=_db,
    user_id=_USER_ID,
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
app = FastAPI(title="MOPS Knowledge Lab")

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
            user_id=_USER_ID,
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
    except Exception:
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
            user_id=_USER_ID,
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
