---
name: mermaid-authoring
description: Mermaid diagram syntax, layout constraints, and semantic guidance
globs: ["**/*.md"]
---

# Mermaid Diagram Authoring Skill

**Applies to**: All agents generating Mermaid diagrams

---

## 1. Diagram Type Selection

Pick the type that fits the content. Flowcharts are a good default but not the only option.

| Type | When to use |
|------|-------------|
| `flowchart TD` | Processes, decision trees, workflows |
| `sequenceDiagram` | Request/response flows, API interactions, ordered message passing |
| `stateDiagram-v2` | Lifecycle states, mode transitions |
| `erDiagram` | Data models, entity relationships |
| `classDiagram` | Type hierarchies, interface contracts |
| `gantt` | Schedules, phase timelines |
| `pie` | Proportional breakdowns (use sparingly) |

---

## 2. Layout Direction

- Default to `TD` (top-down) for all diagrams.
- Use `LR` (left-right) only for timelines or explicit horizontal sequences.
- Never use `RL` or `BT`.

---

## 3. Node Labels

- Keep labels short (3-5 words).
- Use `["label"]` for labels containing special characters.
- Use `{"label"}` for decision nodes (diamonds).

---

## 4. Line Breaks and Markdown Syntax

Multline node text must use double quotes around backtick-wrapped text, with the newline inside the backticks. 

**Forbidden**: Do NOT use `<br>` or `<br/>` in repo Markdown (due to sanitisation rules).

**Correct**:
```
A["`one
two`"]
```

Additionally, use this markdown string syntax (`["` ... `"]`) when you need bold (`**`), or italics (`*`) inside labels.

---

## 5. Design Philosophy

- Diagrams must clarify, not merely decorate. Avoid generating diagrams that do not add structural or sequential clarity to the text.
- Provide a justification if deviating from the default `TD` layout.
