# Bugs: {Service}

---

## Format

```
[STATUS] | #ID | {actual} INSTEAD {expected} | {location} | {learnings} |
```

---

## Tracker

| Status | ID | Issue | Location | Learnings |
|--------|-----|-------|----------|-----------|
| TODO | #DATA-001 | Hardcoded ticker INSTEAD fetch from search | `routers/ohlcv.py:85` | |
| TODO | #DATA-002 | Cache stale after TTL INSTEAD refetch | `storage/cache.py:142` | |
| DOING | #DATA-003 | Retry fires immediately INSTEAD exponential backoff | [ts#data-003] | Verify test assertions before assuming impl is broken |
| DOING | #DATA-007 | Cache refresh races INSTEAD coordinate | [ts#data-007] | Don't hold locks across async boundaries |
| DONE | #DATA-004 | 404 on empty INSTEAD 400 | `routers/ohlcv.py:92` | |

[ts#data-003]: troubleshooting-data-service.md#data-003
[ts#data-007]: troubleshooting-data-service.md#data-007

---

## Summary

| Status | Count |
|--------|-------|
| TODO | 2 |
| DOING | 2 |
| DONE | 1 |

---

## Notes

- Location is `file:line` for straightforward bugs; a link to a separate investigation file for complex ones
- Learnings column: one-line insight from troubleshooting (prevents repeat attempts)
