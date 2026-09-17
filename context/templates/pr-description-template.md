# PR Description Template

---

## Format

```markdown
## Summary

<1-3 sentence description of what this PR accomplishes>

## Changes

| Task | Description | Status |
|------|-------------|--------|
| #ID | Brief description | Done/Partial |

## Agent Metrics

### Efficiency

| Metric | Total | Mean | SD |
|--------|-------|------|----|
| Commits | <count> | — | — |
| Duration | <total> | <mean> | <sd> |
| Tokens (in) | <total> | <mean> | <sd> |
| Tokens (out) | <total> | <mean> | <sd> |

### Autonomy

| Mode | Count | % |
|------|-------|----|
| Fully autonomous | <n> | <pct> |
| With human input | <n> | <pct> |
| Human-directed | <n> | <pct> |

## Test Plan

- [ ] <verification step>

## Links

- [Task details](tasks.md)

---
Generated with [Claude Code](https://claude.ai/code)
```

---

## Section Details

### Summary (required)

One to three sentences. What does this PR do and why?

```markdown
## Summary

Implements webhook retry logic with exponential backoff. Addresses reliability
issues where failed endpoints were overwhelmed by immediate retries.
```

### Changes (required)

Table linking to task IDs with brief descriptions:

```markdown
## Changes

| Task | Description | Status |
|------|-------------|--------|
| DATA-003 | Add retry queue for failed webhooks | Done |
| DATA-004 | Implement exponential backoff logic | Done |
| DATA-005 | Add circuit breaker for repeated failures | Partial |
```

### Agent Metrics (required for agent PRs)

Aggregated from `git log --format='%b' | grep Agent-Session` on the branch. All stats derived from Agent-Session fields across commits.

```markdown
## Agent Metrics

### Efficiency

| Metric | Total | Mean | SD |
|--------|-------|------|----|
| Commits | 12 | — | — |
| Duration | 3h 45m | 18.8m | 12.1m |
| Tokens (in) | 245.3K | 20.4K | 8.2K |
| Tokens (out) | 18.7K | 1.6K | 0.9K |

### Autonomy

| Mode | Count | % |
|------|-------|----|
| Fully autonomous | 8 | 67% |
| With human input | 3 | 25% |
| Human-directed | 1 | 8% |
```

**Autonomy classification** (derived per commit):
- **Fully autonomous**: `dispatch=orchestrator` and `interactions=0`
- **With human input**: `dispatch=orchestrator` and `interactions>0` — delegated but human guided
- **Human-directed**: `dispatch=human`

Counts are the **total human cost** per task — orchestrator + subagent touchpoints summed. Commits without these fields (pre-change) default to human-directed.

### Test Plan (required)

Checklist of verification steps:

```markdown
## Test Plan

- [ ] Unit tests pass (`uv run pytest` / `yarn test --run`)
- [ ] Integration tests pass (`uv run pytest tests/integration`)
- [ ] Manual verification of retry behaviour
- [ ] Load test with simulated failures
```

### Links (required)

Always link to task details:

```markdown
## Links

- [Task details](tasks.md)
- [Relevant ADR](docs/adr/003-webhook-retry-strategy.md)
```

### Footer (required for agent PRs)

```markdown
---
Generated with [Claude Code](https://claude.ai/code)
```

---

## Complete Example

```markdown
## Summary

Implements webhook retry logic with exponential backoff to improve reliability
when downstream services are temporarily unavailable.

## Changes

| Task | Description | Status |
|------|-------------|--------|
| DATA-003 | Add retry queue for failed webhooks | Done |
| DATA-004 | Implement exponential backoff (base 2, max 5 attempts) | Done |
| DATA-005 | Add circuit breaker for repeated failures | Done |

## Agent Metrics

### Efficiency

| Metric | Total | Mean | SD |
|--------|-------|------|----|
| Commits | 4 | — | — |
| Duration | 2h 15m | 33.8m | 10.7m |
| Tokens (in) | 45.2K | 11.3K | 2.6K |
| Tokens (out) | 28.1K | 7.0K | 1.4K |

### Autonomy

| Mode | Count | % |
|------|-------|----|
| Fully autonomous | 2 | 50% |
| With human input | 1 | 25% |
| Human-directed | 1 | 25% |

## Test Plan

- [x] Unit tests pass
- [x] Integration tests with mock failing endpoint
- [ ] Manual verification in staging
- [ ] Load test with 10% simulated failures

## Links

- [Task details](tasks.md#data-003)
- [Blocker resolution](services/data-service/context/domain-rules.yaml#DATA-042)

---
Generated with [Claude Code](https://claude.ai/code)
```

---

## Human-Only PRs

Omit Agent Metrics section and footer:

```markdown
## Summary

Updates API documentation for new webhook endpoints.

## Changes

| Task | Description | Status |
|------|-------------|--------|
| DOC-001 | Document retry behaviour | Done |

## Test Plan

- [x] Documentation renders correctly
- [x] Code examples verified

## Links

- [Task details](tasks.md)
```
