---
name: ui-testing
description: Procedural guidance for UI testing and browser automation.
globs: ["**/*.test.ts", "**/*.spec.ts"]
---

# UI Testing Skill

---

## Overview
Procedural guidance for browser automation, UI inspection, screenshot capture, and E2E test phases.

---

## 1. Tool Selection by Capability

When browser automation is required, prefer tools in this strict order:
1. **Built-in Runtime Browser**: Many runtimes (like Antigravity) have a built-in browser (e.g., via MCP tools). Prefer using this first.
2. **`puppeteer-core`**: Use for headless scripts in terminal environments. Ensure you connect to an existing Chrome instance or launch via `executablePath`.

---

## 2. Headless Script Pattern (`puppeteer-core`)

When writing a puppeteer script, use the following boilerplate:

```typescript
import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});
const page = await browser.newPage();
await page.goto('http://localhost:3000');
const screenshot = await page.screenshot({ path: 'screenshot.png' });
await browser.close();
```

**Execution**: Run the script with `yarn dlx tsx script.ts` (never `npx`).

---

## 3. Required Rule Invariants (Enforced via Pre-Commit)
When executing this skill, ensure output satisfies the deterministic rules:
- UI Testing constraints: `context/rules/ui-testing.md`
