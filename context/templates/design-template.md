# Design: {Feature Name}

> This document is the authoritative reference for a single feature or screen. Create it before implementation begins for any feature complex enough that a developer would need to ask clarifying questions. Update it to reflect the as-built state after implementation. Consumed by: python-coder, typescript-coder, functional-tester.

**Status**: {Proposed | In Progress | Current (as-built)}
**Date**: {YYYY-MM-DD of last substantive change}
**Branch**: `{branch-name}`

---

## 1. Purpose and User Flow

{2-4 sentences: what this feature does for the user and why it exists. State the user's goal, not the implementation.}

The typical flow:

1. {First user action or entry point.}
2. {Next step in the happy path.}
3. {Continue until the user's goal is achieved.}

<!-- Include alternative flows or error paths only if they affect the component design. -->

---

## 2. Layout

<!-- An ASCII diagram showing the spatial arrangement of the feature's UI. Use box-drawing characters for structure. Label each region with its component name or role. Omit this section for backend-only features. -->

```
┌──────────────────────────────────────────────────────────────┐
│  {Region A — description}                                     │
├──────────────────┬───────────────────────────────────────────┤
│  {Region B}      │  {Region C}                                │
│  {dimensions}    │  {dimensions or flex behaviour}            │
│                  │                                            │
│                  │                                            │
└──────────────────┴───────────────────────────────────────────┘
```

{1-2 sentences on the layout strategy: flex direction, fixed vs fluid regions, responsive breakpoints, collapse behaviour.}

---

## 3. Component Breakdown

<!-- One subsection per component. Order top-down: parent before children. Each component section should be self-contained — a developer reading only that section should know what to build. -->

### 3.1 {ComponentName}

<!-- Repeat this block for each component. -->

**Role**: {Single sentence — what this component is responsible for.}

**Props / Inputs**:

| Prop | Type | Description |
|------|------|-------------|
| {propName} | `{TypeScript or Python type}` | {What it controls} |

**Behaviour**:

- {Describe each interactive behaviour as a concrete rule: "When X happens, Y occurs."}
- {Include edge cases that affect rendering or state.}
- {Reference requirement IDs where they exist, e.g. (REQ-XXX-NNN).}

**Styling notes**: {Only if non-obvious: specific widths, z-index layering, scroll behaviour, or design system tokens used.}

<!-- Include if this component has significant internal state -->
**Local state**:

| State | Type | Initial | Trigger |
|-------|------|---------|---------|
| {stateName} | `{type}` | {initial value} | {What causes it to change} |
<!-- End local state -->

---

## 4. Data Contract

<!-- Define the data shapes that flow into and out of this feature. For frontend features, this means API request/response shapes and component prop types. For backend features, this means function signatures and return types. -->

### API Endpoints

<!-- Omit if this feature uses no API calls. -->

#### `{METHOD} {/path}`

**Purpose**: {What this call achieves for the feature.}

**Request**:

```json
{
  "{field}": "{type — description}"
}
```

**Response**:

```json
{
  "{field}": "{type — description}"
}
```

**Error states**: {List HTTP status codes and their meaning for this feature, or "Standard error handling" if nothing feature-specific.}

### Type Definitions

<!-- Key types that multiple components in this feature share. Use TypeScript or Python syntax matching the implementation language. -->

```typescript
interface {TypeName} {
  {field}: {type};  // {description}
}
```

---

## 5. State Model

<!-- How state flows through this feature. Show ownership (which component owns the state), data flow direction, and persistence. Omit for stateless features. -->

### State Ownership

```
{ParentComponent}  ← owns {stateA}, {stateB}
├── {ChildA}       ← reads {stateA}, calls onChange
└── {ChildB}       ← reads {stateB}
    └── {GrandChild} ← local state only
```

### Persistence

<!-- Omit if no state is persisted. -->

| State | Storage | Key | Sync Behaviour |
|-------|---------|-----|----------------|
| {stateName} | {localStorage / server / none} | `{storage-key}` | {e.g. Debounced PUT on change, restored on mount} |

### Context Dependencies

<!-- Omit if the feature uses no shared context. -->

| Context | Hook | Usage in this feature |
|---------|------|-----------------------|
| {ContextName} | `{useHookName}` | {What data or actions this feature reads/calls} |

---

## 6. States and Conditions

<!-- Enumerate the distinct visual or behavioural states the feature can be in. This table is the source of truth for what the user sees under each condition. -->

| Condition | Display | Test ID / Notes |
|-----------|---------|-----------------|
| {e.g. Loading} | {What the user sees} | {`data-testid` or implementation note} |
| {e.g. Empty results} | {What the user sees} | |
| {e.g. Error} | {What the user sees} | |
| {e.g. Normal} | {What the user sees} | |

---

## 7. Acceptance Criteria

<!-- Testable statements that define "done" for this feature. Each criterion should be verifiable by a functional-tester agent without ambiguity. Use the Given/When/Then format or simple declarative statements. -->

- [ ] {Given {precondition}, when {action}, then {expected outcome}.}
- [ ] {Given {precondition}, when {action}, then {expected outcome}.}
- [ ] {Component renders {specific element} when {condition}.}
- [ ] {State persists across {action} — verified by {method}.}

---

## 8. Open Questions

<!-- Unresolved decisions that may affect implementation. Remove entries as they are resolved — do not leave stale questions. If no open questions remain, delete this section entirely. -->

| # | Question | Impact | Owner |
|---|----------|--------|-------|
| 1 | {Unresolved question} | {What is blocked or uncertain} | {Who should decide} |

---

## 9. Component Hierarchy

<!-- A tree showing the full component nesting for this feature. Useful for agents that need to understand the render tree at a glance. -->

```
{RootComponent}
├── {ChildA}
│   ├── {GrandChildA1}
│   └── {GrandChildA2}
├── {ChildB}
│   └── {GrandChildB1}
└── {ChildC}
```

---

## 10. Related Documents

<!-- Link to documents that provide additional context. Do not duplicate their content here. -->

- `{architecture.md}` — system-level context and service boundaries
- `{other-design-doc.md}` — related feature design
- `{design-system.md}` — component library and styling conventions
- `{data-model.md}` — shared type definitions and field semantics
