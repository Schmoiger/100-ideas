---
description: TypeScript/JavaScript environment setup and command execution
globs: ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/package.json"]
alwaysApply: false
---

# TypeScript Environment

**Applies to**: All TypeScript/JavaScript code execution

---

## Strict Invariants

1. **NEVER use `npm` or `npx`. ALWAYS use `yarn` and `yarn dlx`.**
2. Each TypeScript project must use `yarn.lock` (never `package-lock.json`) and must be explicitly listed in the root `package.json` workspaces array.
3. Install packages at the project root folder, not at the monorepo root.
4. `tsconfig.json` MUST have `strict: true`, `noImplicitAny: true`, and `strictNullChecks: true` enabled.
5. **Forbidden**: Using `any` type (use `unknown` instead), `// @ts-ignore` without a documented reason, or disabling strict checks.

---

## Banned Commands & Tool Substitutions

| Action | Required | Forbidden |
|--------|----------|-----------|
| Run tests | `yarn test` | `npm test` |
| Install package | `yarn add package` | `npm install package` |
| Install dev package | `yarn add -D package` | `npm install --save-dev package` |
| Install all deps | `yarn install` | `npm install` |
| Run script | `yarn scriptname` | `npm run scriptname` |
| Execute binary | `yarn dlx package` | `npx package` |
| Lint (from any directory) | `yarn --cwd {repo-root} run lint` | `yarn lint` (from subdirectory) |
