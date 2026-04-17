# Agent-Aware Welcome State

Replace Agno-branded chat blank state with a contextual welcome that shows the selected agent's name and description.

## Problem

When a user selects an agent, the chat area shows a generic Agno open-source promo with external links to AgentOS and documentation. This is irrelevant to MOPS Knowledge Lab users and wastes prime screen real estate.

## Solution

Replace `ChatBlankState` with an agent-aware welcome that displays the selected agent's name and description. When no agent is selected, show the MOPS Knowledge Lab name with a prompt to select an agent.

## Changes

### 1. `ui/src/types/os.ts` — Add description to AgentDetails

Add `description?: string` to the `AgentDetails` interface. The backend already returns this field; the frontend simply discards it.

### 2. `ui/src/components/chat/ChatArea/Messages/ChatBlankState.tsx` — Rewrite

Delete all Agno content (links, tech icons, action buttons, tooltip animations). Replace with:

- Read `agents` from `useStore()` and `agent` query param from `useQueryState('agent')`
- Find the matching agent to get its name and description
- **Agent selected:** Show agent name (large heading) + description (muted subtext) + "Ask me anything" prompt
- **No agent selected:** Show "MOPS Knowledge Lab" heading + "Select an agent to get started" subtext
- Keep framer-motion fade-in animation for polish

### 3. No backend changes

The `/agents` endpoint already returns `description`. No changes needed.

## Out of Scope

- Agent-specific icons or avatars
- Suggested starter prompts per agent
- Sidebar branding changes (Agno icon in sidebar header is separate)
