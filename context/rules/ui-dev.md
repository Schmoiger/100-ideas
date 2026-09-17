---
description: Strict code-state invariants for UI component styling
globs: ["**/*.tsx", "**/*.css", "**/*.scss"]
alwaysApply: false
---

# UI Development Invariants

These are the strict, zero-token verifiable rules for UI styling and component creation.

---

## Forbidden Styling Practices

- **NEVER use `!important`** or specificity hacks.
- **NEVER hardcode colour values** (e.g., raw hex codes). Semantic tokens must be used.
- **NEVER create `.css`/`.scss` files** for component styling without first exhaustively attempting to use DaisyUI and Tailwind utilities.
