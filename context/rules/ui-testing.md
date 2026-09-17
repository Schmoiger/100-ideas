---
description: Strict dependencies and constraints for UI testing
globs: ["**/*.test.ts", "**/*.spec.ts", "package.json"]
alwaysApply: false
---

# UI Testing Invariants

These are the strict, zero-token verifiable rules for browser automation and UI testing.

---

## 1. Forbidden Dependencies

- **NEVER run `yarn add puppeteer`**: The project strictly uses `puppeteer-core`.
- **NEVER install Playwright or Cypress**: These frameworks are too heavy and are explicitly banned.

---

## 2. Forbidden Actions

- **NEVER use ad-hoc browser-installing subagents**: They tend to install full browser binaries into `frontend/package.json` and pollute dependencies and lockfiles.
