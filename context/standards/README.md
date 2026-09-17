---
purpose: Index and guide to all standards documents
audience: All agents and developers
read-when: Navigating standards, understanding what to read
---

# Standards Index

---

## Standards Map

| Standard | Purpose | Read when | Not for |
|----------|---------|-----------|---------|
| [tech-standards](tech-standards.md) | Tool and platform choices | Tech choices, project setup | Testing methodology, code patterns |
| [testing-standards](testing-standards.md) | Testing methodology and TDD | Writing tests, coverage | Tool installation |
| [coding-standards](coding-standards.md) | Code patterns and structure | Writing code, reviewing PRs | Tool choices |
| [security-standards](security-standards.md) | Security principles | Auth design, data handling | Implementation details |
| [build-standards](build-standards.md) | CI/CD and deployment | Pipelines, deploying | Tech stack choices |
| [doc-standards](doc-standards.md) | Documentation structure | Writing docs, artefacts | Code patterns |
| [workflow-standards](workflow-standards.md) | Development process | Starting work, TDD flow | Tool choices |
| [agent-standards](agent-standards.md) | Agent behaviour and tools | Agent setup, tool usage | Tech stack |
| [visual-standards](visual-standards.md) | Visual design standards | UI design | Backend, API |
| [LESS-Engineering-Principles](LESS-Engineering-Principles.md) | Design philosophy | Architecture decisions | Implementation detail |
| [12-factor-principles](12-factor-principles.md) | SaaS application patterns | Designing services | Frontend, mobile |
| [tech-mobile-standards](tech-mobile-standards.md) | Mobile tech stack (deferred) | Mobile development | Web, backend |

---

## DRY Principle

Each topic lives in **one** authoritative place. Other standards cross-reference rather than duplicate. If you find the same guidance in two places, the standard listed in the "Purpose" column above is the authority.

---

## Frontmatter Convention

All standards use YAML frontmatter with: `purpose`, `audience`, `read-when`, `not-for`, `related`.
