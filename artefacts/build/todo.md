[x] Review folder structure in bollinger project and figure out which best practice to standardise in start-here project. For example: whether to use /build folder or /handoff.
[x] Review agents for DRY compliance. For example: @python-coder has assumptions on tech (Pytest) embedded whereas it should look at tech-standards.md
[x] Create agent that specifically looks at the effectiveness of other agents, i.e. efficient tokenomics.
[x] Update all start-here /context from bollinger /context
[x] When agents commit they should push as well (to protect from accidental deletion) - update agent-standards
[x] When an orchestrator spawns a sub-agent does it give the right context files (rules, standards)? They always seem to forget.
[WON'TDO] Keep both context and context-compressed folders - don't know which is more effective yet.
[x] Update the readme
[x] Adopt British English 'artefact' convention
[x] Workflow should have tasks.md for tracking
[x] Add persona (e.g. Dr. Sarah Chen from new-dev)
[x] Formalise the parallel workflow. Solution architect identifies 1) context domains and 2) dependencies between context domains (blocking points). Tasks are written as phases = work between blocking points. Each domain works in parallel up to those blocking points. Within each domain there might be further opportunities for parallel working. At blocking points tech-lead then solution-architect does quality verification. A diagram will help.
[x] We have security agent at the end. Better is to have LESS agents by-design = at QA points: architecture, tasks, blocking points. Bugs are added and fixed before proceeding.
[x] For full YOLO mode how can we have some bash commands authorised and not others? Need a risk rating surfaced with all human intervention requests.
[x] Add section in agent-standards on agent invocation because it's not in the expected .claude/agents way
[x] Merge ui-designer and visual-designer agents
[x] Add template for settings.local.json
[ ] Check standards are DRY, do not include code samples, even no installation notes (tech-standards needs work)
[x] Investigate Option 2 (Failure-Mode Transparency / Fail-Fast Rule): Update agent-standards with an explicit invariant forbidding silent tool substitution when standard-mandated tools (e.g. uv, yarn dlx) fail.
[ ] Investigate Option 4 (Comprehensive Pre-Commit Validators): Upgrade british_english.py beyond a hardcoded list to comprehensive dictionary-based checks (e.g. pyspelling/Hunspell) and add pre-commit enforcement against forbidden toolchains.
[x] Remove `context/scripts/coordinate.sh` — superseded by YAML workflow definitions (`context/workflows/*.yaml`) and agent runtime orchestration.
[x] Fix `prepare-commit-msg` git hook and telemetry extraction via the runtime adapter layer (install hook symlink, support Claude Code, Antigravity, and Codex session telemetry per `context/models.yaml`).
[ ] Replace per-repo context in existing repositories (e.g. bollinger) with the canonical standards subrepo (`git subrepo clone git@github.com:Schmoiger/start-here.git context -b standards`).
[ ] Configure GitHub Actions secrets and variables in repository settings (`ANTHROPIC_API_KEY` in Secrets, `RUN_LLM_TESTS` in Variables) to support CI LLM consistency testing.
