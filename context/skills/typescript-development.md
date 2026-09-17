---
name: typescript-development
description: Procedural guidance for setting up and working with TypeScript/JavaScript projects using Yarn Berry workspaces.
globs: ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/package.json"]
---

# TypeScript Development Skill

---

## Overview
Procedural guidance for setting up TypeScript workspaces and configuring tooling. All commands executed under this skill are subject to the invariants defined in `context/rules/typescript-environment.md`.

---

## 1. Project Setup
Each TypeScript project must have:
- `package.json` with dependencies
- Listed in root `package.json` workspaces array
- Use `yarn.lock` (never `package-lock.json`)

Install packages at the project root folder, not at the monorepo root. This ensures proper dependency isolation.
```bash
cd {project-root}
yarn add package-name
```

---

## 2. Yarn Berry Setup

**Installation:**
```bash
# Enable Corepack (ships with Node.js 16.10+)
corepack enable

# In your project
yarn init -2              # New project
yarn set version stable   # Existing project
```

Corepack downloads the Yarn version specified in `package.json` (`"packageManager": "yarn@4.1.0"`).

**One-off tools:** Use `yarn dlx` (not `npx`).

**Exception — MCP servers:** Model Context Protocol server configs (e.g. in `context/mcp/mcp.json`) may use `npx` because the MCP host (e.g. Cursor) often runs outside the project environment and may not have the project's Yarn on PATH.

**Common issues:**
- "yarn: command not found" → `corepack enable`
- Homebrew conflict → `brew uninstall yarn`

---

## 3. Pre-commit Hooks (Husky & Biome)
To configure pre-commit hooks for a frontend TypeScript project:

```bash
yarn add -D @biomejs/biome husky
npx husky init
echo "npx biome check --apply src/" > .husky/pre-commit
echo "npx tsc --noEmit" >> .husky/pre-commit
```

---


## 5. Procedural Execution Commands

### Setup and Environment
```bash
# Install dependencies across all workspaces
yarn install

# Add dependencies to a specific project
cd frontend/{app-name}
yarn add package-name
yarn add -D dev-package-name
```

### Testing and Coverage
```bash
# Run tests
yarn test

# Run tests with coverage
yarn test --coverage
```

---

## 6. Rationale
- **Why Yarn workspaces:** Using npm breaks workspace dependency resolution, creates conflicting lock files (`package-lock.json` vs `yarn.lock`), and may install wrong versions.
- **Workspace Management:** Root `package.json` workspaces array must be explicitly maintained (no wildcards). This prevents accidental inclusion of incomplete/broken projects and Python projects.
- **Why Type Safety:** Strict mode catches errors at compile time, enables IDE autocomplete, documents expected data shapes, and makes refactoring safer.
