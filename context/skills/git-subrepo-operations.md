---
name: git-subrepo-operations
description: Procedural guidance and constraints for managing canonical context using git-subrepo
globs: ["**/.gitrepo", "context/**", "typst/**"]
---

# Git Subrepo Operations Skill

**Applies to**: Any modification, synchronisation, status check, or operation involving `.gitrepo` tracked directories (e.g., `context/`, `typst/`).

---

## 1. Core Constraints

When operating on `.gitrepo` tracked directories, you **MUST NOT**:
- Use native Git submodule commands (e.g., `git submodule update`, `git submodule add`).
- Manually edit the `.gitrepo` tracking state file (it records remote URLs, branch names, commit hashes, and merge parents deterministically).
- Run `git push` or `git pull` from inside the subfolder using standard Git remotes.

Instead, you **MUST** use the `git-subrepo` extension. If the command is missing on the host machine, prompt the user to install it (`brew install git-subrepo`).

---

## 2. macOS PATH Prepending Requirement

Non-login subshells spawned by agents default to `/bin/bash` (macOS default v3.2), which triggers a fatal bash version check error because `git-subrepo` requires Bash 5+. Modern Homebrew Bash is already installed at `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/bin` (Intel).

- **DO NOT** attempt to install bash via brew or probe for alternate shells.
- **ALWAYS** prepend the Homebrew binary directories to `PATH` on every `git subrepo` command.

**Correct Command Shape**:
```bash
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo <subcommand>
```

---

## 3. Subrepo Inspection (`status`)

Before pulling or pushing, inspect the current synchronisation status of the tracked subrepo:

```bash
# Check status of context/ subrepo
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo status context

# Check status of typst/ subrepo
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo status typst
```

The output displays:
- **Subrepo Directory**: Local folder path.
- **Remote URL**: Upstream canonical repository.
- **Tracking Branch**: The remote branch being tracked (e.g. `main` or `standards`).
- **Commit Status**: Indicates whether the local subrepo is up-to-date, ahead of upstream, or behind upstream.

### Automated Freshness Validator
To programmatically check whether your branch's tracked subrepos have diverged from upstream:

```bash
uv run python context/scripts/validators/subrepo_freshness.py
```
This validator runs automatically in `.github/workflows/pr-subrepo-checks.yml` on pull requests modifying subrepo paths.

---

## 4. Pulling Upstream Changes (`pull`)

To pull updates from the canonical remote repository into your local subrepo:

### Prerequisites
`git status` **MUST** be clean before executing `git subrepo pull`.

### Standard Pull
```bash
# Pull upstream updates for context/
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo pull context

# Pull from a specific branch if different from default
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo pull context -b main
```

### Pulling with Uncommitted Changes in Parent Repo
If you have uncommitted changes in the parent repository:
```bash
git stash
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo pull context
git stash pop
```

`git subrepo pull` fetches upstream commits, merges them into the local directory, and automatically creates a merge commit in the parent repository updating `.gitrepo`.

---

## 5. Pushing Local Changes Upstream (`push`)

To push local changes made to a subrepo back to the canonical upstream repository:

### Governance and Push Timing

> [!WARNING]
> **Push Gate: NEVER push directly to upstream `main` from an in-flight feature branch.**
> Upstream canonical repositories (such as `agents-framework` and `typst-engine`) are shared across multiple projects. Pushing unreviewed changes directly to upstream `main` immediately pollutes the canonical source of truth for all projects and causes commit history divergence.

Subrepo pushes must follow one of two approved lifecycles:

1. **Post-Merge Upstream Push (Standard)**:
   - Changes to the subrepo are committed, reviewed, and merged into the host repository's `main` branch via PR first.
   - Once merged into `main`, push to the upstream remote `main` branch from the host repository `main` branch.

2. **Upstream Feature Branch (Cross-Repo Review)**:
   - If upstream validation or a pull request in the canonical repository is needed *before* merging into the host repository:
     ```bash
     PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo push <dir> -b feature/<branch-name>
     ```
   - Open a PR against `main` directly in the canonical repository.

### Step 1: Commit Local Changes in Parent Repo
First, ensure all modifications within the subrepo directory are committed in the parent repository:
```bash
git add context/
git commit -m "feat(context): add new validator and update rules"
```
The working tree **MUST** be clean (`git status` reports nothing to commit).

### Step 2: Push to Upstream Subrepo Remote
```bash
# Push context/ commits upstream (from main post-merge)
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo push context

# Or push to an upstream feature branch for cross-repo review
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo push context -b feature/my-branch
```

### What Happens During Push
1. `git-subrepo` calculates all commits in the parent repository touching the subrepo directory since the last sync.
2. It generates a synthetic branch and pushes those commits to the upstream repository.
3. It automatically creates a new commit in the parent repository updating `.gitrepo` with the new upstream commit hash (with commit message `git subrepo push <dir>`).

### Automated 3-Way Reconciliation on Merge
When PRs are merged into `main`, `.github/workflows/pr-subrepo-push.yml` automatically evaluates whether the upstream canonical repository has moved ahead:
1. If upstream has newer commits, the workflow automatically runs `git subrepo pull <subdir>` first to merge upstream changes cleanly before pushing.
2. The combined result is pushed upstream to the canonical repository, and updated tracking commits are pushed back to `main`.
3. If semantic merge conflicts occur, the workflow halts safely and outputs actionable recovery commands to `$GITHUB_STEP_SUMMARY`.

### Force Pushing
If upstream history has been rebased or diverged:
```bash
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo push context --force
```
*Exercise caution with `--force` and verify upstream branches before running.*

---

## 6. Cloning a New Subrepo (`clone`)

To add a new subrepo into an existing repository:

```bash
# Clone the canonical agents-framework into context/
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo clone https://github.com/Schmoiger/agents-framework.git context -b main

# Clone the typst-engine into typst/
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo clone https://github.com/Schmoiger/typst-engine.git typst -b main
```

---

## 7. Cleaning Temporary State (`clean`)

If a pull, push, or merge operation is aborted or fails halfway, temporary branch or merge state may remain. Clean up with:

```bash
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" git subrepo clean context
```

---

## 8. Banned Operations

| Operation | Allowed / Required | Strictly Forbidden |
|---|---|---|
| Pull updates | `PATH="..." git subrepo pull <dir>` | `git pull`, `git submodule update` |
| Push updates | `PATH="..." git subrepo push <dir>` | `cd <dir> && git push`, native git submodules |
| Inspect sync | `PATH="..." git subrepo status <dir>` | Comparing raw SHAs manually |
| State changes | Handled by `git-subrepo` commands | Manually editing `<dir>/.gitrepo` |
| Environment | Prepend `PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"` | `brew install bash` (already installed) |
| Dirty working tree | Stash uncommitted changes prior to pull/push | Running subrepo commands on dirty trees |
| Push timing | Push to upstream `main` only post-merge (or to `-b feature/...`) | Pushing directly to upstream `main` from an unapproved feature branch |
