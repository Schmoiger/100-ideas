# Agent Inventory

| Agent | Model | Purpose |
|-------|-------|---------|
| **orchestrator** | large | Coordinates workflow execution, delegates to specialised agents, manages quality gates |
| | | |
| **product-expert** | large | Elicits and clarifies vague ideas into requirements through conversation |
| **product-owner** | medium | Transforms requests into structured requirements and user stories |
| | | |
| **solution-architect** | large | Designs system architecture, component boundaries, and data flow |
| **database-designer** | medium | Designs schemas, relationships, and migrations |
| **api-designer** | medium | Designs APIs with OpenAPI specifications |
| **ui-designer** | medium | Designs UI layouts, component specs, design systems, and visual assets |
| | | |
| **python-coder** | medium | Writes production Python code |
| **typescript-coder** | medium | Builds frontend and backend TypeScript |
| **functional-tester** | medium | Writes and runs TDD tests for Python and TypeScript |
| | | |
| **tech-lead** | medium | Reviews code for architecture compliance — THE GATE |
| **code-reviewer** | medium | PR-style review focusing on bugs, edge cases, and maintainability |
| **principles-reviewer** | large | Reviews designs and implementations against LESS Engineering Principles |
| **security-tester** | medium | Identifies vulnerabilities via threat modelling and code analysis |
| | | |
| **ui-tester** | small | Tests UI behaviour using browser automation |
| **devops** | small | Deploys and validates infrastructure |
| **documentation** | medium | Generates user-facing docs, API references, and guides |
| | | |
| **workflow-analyst** | medium | Analyses workflow efficiency for retrospectives |
| **tokenomics-analyst** | medium | Audits agent effectiveness, token economics, and model tiering |

*Note: Model tiers (small, medium, large) are mapped to specific provider models via `context/models.yaml`.*
