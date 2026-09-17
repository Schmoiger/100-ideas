---
description: Strict invariants for agent handoffs and escalations
globs: []
alwaysApply: false
---

# Multi-Agent Collaboration Invariants

**Applies to**: All agents engaged in multi-agent workflows (e.g. subagents, orchestrators) or handing off tasks.

---

## 1. Escalation

1. **Escalate High-Impact Uncertainty**: If you face ambiguity where being wrong has a high impact (e.g., architectural decisions, scope creep, data loss), you MUST STOP and escalate.
2. **Subagents Escalate to Orchestrator**: Subagents NEVER escalate directly to the human. They must write their escalation notes into the handoff and return control to the Orchestrator.
3. **Orchestrator Escalates to Human**: The Orchestrator alone decides whether to resolve an escalation or forward it to the human (see `context/skills/multi-agent-workflows.md` for triage matrix).

---

## 2. Handoff Hygiene

1. **Always Update Tracking Files**: After every task, you MUST update `tasks.md`, `bugs.md`, and `todo.md` if applicable.
2. **Always Update HANDOFF.md**: You MUST write your handoff notes to `artefacts/build/HANDOFF.md` (or the service-specific equivalent).
3. **Never Declare Success Early**: Do not mark a task as complete in the handoff if you were blocked or escalated.
