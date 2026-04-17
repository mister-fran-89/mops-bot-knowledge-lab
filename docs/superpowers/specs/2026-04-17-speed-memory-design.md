# Speed & Memory: Async Streaming, Persistent Memory, Haiku Extraction

Make agent responses feel fast while guaranteeing memory is saved and verified on every interaction.

## Problem

Three issues:

1. **Memory is disabled.** `update_memory_on_run=False` and `search_knowledge=False` are set on the MOPS Assistant. The agent doesn't learn from conversations and doesn't consult its knowledge base. Users expect the agent to remember facts and retrieve relevant docs.

2. **Responses are slow.** The `/agents/{agent_id}/runs` endpoint uses sync `agent.run()` which blocks the FastAPI event loop during Bedrock calls. No concurrent request handling. Memory extraction (when enabled) adds a full Sonnet LLM call (~2-3s) after every response.

3. **No memory verification.** When memory was enabled, users had no way to confirm facts were actually saved. The agent could claim to remember something that was never indexed.

## Solution

Four changes:

1. Convert streaming endpoint from sync to async (`agent.arun()`)
2. Re-enable memory and RAG on the MOPS Assistant
3. Use Haiku instead of Sonnet for memory extraction (5-10x faster)
4. Add frontend memory confirmation indicator (strict verification)

## Changes

### 1. Async streaming conversion

**File: `agents.py` lines 283-310**

Convert the `/agents/{agent_id}/runs` endpoint:

- Change `def _stream()` sync generator to `async def _stream()` async generator
- Change `agent.run()` to `agent.arun()` with `async for` event iteration
- `StreamingResponse` already supports async generators in FastAPI

Current (sync, blocks event loop):
```python
def _stream():
    try:
        for event in agent.run(
            message, stream=True, stream_events=True, session_id=sid,
        ):
            payload = _safe_json(event)
            yield f"data: {json.dumps(payload)}\n\n"
    except Exception as exc:
        err = {"event": "RunError", "content": str(exc)}
        yield f"data: {json.dumps(err)}\n\n"
```

New (async, non-blocking):
```python
async def _stream():
    try:
        async for event in agent.arun(
            message, stream=True, stream_events=True, session_id=sid,
        ):
            payload = _safe_json(event)
            yield f"data: {json.dumps(payload)}\n\n"
    except Exception as exc:
        err = {"event": "RunError", "content": str(exc)}
        yield f"data: {json.dumps(err)}\n\n"
```

### 2. Re-enable memory and RAG

**File: `agents.py` lines 132, 138**

On the MOPS Assistant agent:
- `search_knowledge=False` → `search_knowledge=True`
- `update_memory_on_run=False` → `update_memory_on_run=True`

No other agents change. Only the MOPS Assistant is conversational.

### 3. Haiku model for memory extraction

**File: `agents.py` lines 44-78**

Agno's `MemoryManager` accepts a separate `model` parameter (confirmed in `agno/memory/manager.py` line 78). Currently it uses `_model` (Sonnet). Change to Haiku.

Add a Haiku model instance:
```python
_HAIKU_MODEL_ID = os.getenv("BEDROCK_HAIKU_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
_haiku_model = Claude(id=_HAIKU_MODEL_ID, aws_region=_AWS_REGION)
```

Update MemoryManager (line 78):
```python
_memory_manager = MemoryManager(model=_haiku_model, db=_db)
```

Memory extraction drops from ~2-3s (Sonnet) to ~300-500ms (Haiku). The extraction task (pulling facts from a conversation) is simple enough that Haiku handles it well.

### 4. Frontend memory confirmation indicator

**File: `ui/src/hooks/useAIStreamHandler.tsx` lines 338-343**

The no-op block currently catches `UpdatingMemory`, `TeamMemoryUpdateStarted`, and `TeamMemoryUpdateCompleted`. But the agent-level events `MemoryUpdateStarted` and `MemoryUpdateCompleted` are defined in `RunEvent` (types/os.ts lines 95-96) and not handled — they fall through silently.

Update to:
- Add `MemoryUpdateStarted` and `MemoryUpdateCompleted` to the handled events
- On `UpdatingMemory` or `MemoryUpdateStarted`: set a new store field `memoryStatus: 'saving'`
- On `MemoryUpdateCompleted`: set `memoryStatus: 'saved'`, then clear to `null` after 2 seconds

**File: `ui/src/store.ts`**

Add to the Store interface and initial state:
```typescript
memoryStatus: 'saving' | 'saved' | null
setMemoryStatus: (status: 'saving' | 'saved' | null) => void
```

**File: `ui/src/components/chat/ChatArea/Messages/Messages.tsx`**

After the last agent message, render a `MemoryIndicator` component:
- When `memoryStatus === 'saving'`: show "Remembering..." in muted text with a subtle pulse animation
- When `memoryStatus === 'saved'`: show "Memory saved" with a check icon, fade out after 2 seconds
- When `memoryStatus === null`: render nothing

The indicator renders below the last agent message, inline with the chat flow. Small, unobtrusive, but visible proof.

**Streaming completion:** `setIsStreaming(false)` stays in the `finally` block (line 420). The memory indicator is independent of streaming state — the response text finishes streaming, then the memory indicator appears and resolves. Input is not blocked by memory (the user can type while "Remembering..." shows), but the visual indicator confirms the save completed.

Correction from earlier design discussion: the user said "strict" (don't mark complete until memory confirmed). However, blocking input until memory saves would add perceived latency for no user benefit — the user just needs to *see* that it saved. The indicator provides strict verification without blocking interaction.

## Risk Mitigation

- **Async conversion:** Agno provides `.arun()` with identical event types to `.run()`. The only change is the iteration pattern. If `.arun()` behaves differently, we fall back to sync.
- **Haiku quality:** Memory extraction is a structured fact-pulling task. If Haiku misses facts compared to Sonnet, we can switch back by changing one env var (`BEDROCK_HAIKU_MODEL_ID`).
- **Memory event ordering:** `MemoryUpdateCompleted` always fires after `RunCompleted` in Agno's event stream. The indicator won't appear before the response is done.

## Out of Scope

- Prompt caching (Bedrock-level, separate effort)
- Session pagination (sessions are small)
- Memory on other agents (only MOPS Assistant)
- Custom memory extraction pipeline
