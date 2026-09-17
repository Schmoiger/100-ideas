#!/usr/bin/env python3
"""prepare-commit-msg hook: append token usage to Agent-Session trailer.

Extracts session telemetry across multiple AI runtimes:
- Claude Code (~/.claude/projects/)
- Google Antigravity (~/.gemini/antigravity-ide/conversations/*.db)
- GitHub Copilot Chat (VS Code workspaceStorage/*/chatSessions/*.jsonl)
- OpenAI Codex / API run steps

Computes token consumption deltas since the last commit and injects or updates
`tokens=<in>K/<out>K` in the `Agent-Session:` trailer of the commit message.

If telemetry extraction fails or schema drift occurs, an error trailer
`tokens=error(<reason>)` is recorded and a diagnostic warning is logged to stderr.
The hook NEVER exits with non-zero exit code to avoid blocking git commit.
"""

from __future__ import annotations

import json
import glob
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Tuple


# =============================================================================
# Data Models & Utilities
# =============================================================================

@dataclass
class ExtractionResult:
    """Result of a runtime telemetry extraction."""
    tokens_in: int = 0
    tokens_out: int = 0
    thinking_tokens: int = 0
    model: Optional[str] = None
    runtime: Optional[str] = None
    error: Optional[str] = None
    watermark_updates: dict[str, Any] = field(default_factory=dict)


def format_tokens(count: int) -> str:
    """Format token count with K or M suffix for human readability."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.2f}M"
    if count >= 1000:
        return f"{count / 1000:.1f}K"
    return str(count)


def get_git_repo_root() -> Optional[str]:
    """Derive the git repository top-level root path."""
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        return root if os.path.isdir(root) else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_watermark_path(repo_root: str, runtime_name: str) -> str:
    """Return the path to the watermark file for a specific runtime."""
    return os.path.join(repo_root, ".git", f".tokens-watermark-{runtime_name}.json")


def read_watermark(watermark_path: str) -> dict[str, Any]:
    """Read stored watermark data."""
    if os.path.exists(watermark_path):
        try:
            with open(watermark_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def write_watermark(watermark_path: str, data: dict[str, Any]) -> None:
    """Persist updated watermark data."""
    try:
        os.makedirs(os.path.dirname(watermark_path), exist_ok=True)
        with open(watermark_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


# =============================================================================
# Pure-Python Lightweight Protobuf Decoder (for Antigravity SQLite telemetry)
# =============================================================================

def _decode_varint(data: bytes, offset: int) -> Tuple[int, int]:
    """Decode a variable-length integer from protobuf wire format."""
    res = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise IndexError("Unexpected end of protobuf buffer while decoding varint")
        b = data[offset]
        offset += 1
        res |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    return res, offset


def parse_protobuf_fields(data: bytes) -> list[Tuple[int, str, Any]]:
    """Parse protobuf wire format into a list of (field_num, wire_type, value)."""
    offset = 0
    fields = []
    while offset < len(data):
        try:
            key, offset = _decode_varint(data, offset)
        except IndexError:
            break
        field_num = key >> 3
        wire_type = key & 0x07

        if wire_type == 0:  # Varint
            val, offset = _decode_varint(data, offset)
            fields.append((field_num, "varint", val))
        elif wire_type == 1:  # 64-bit
            val = data[offset:offset + 8]
            offset += 8
            fields.append((field_num, "fixed64", val))
        elif wire_type == 2:  # Length-delimited (string, bytes, embedded message)
            length, offset = _decode_varint(data, offset)
            val = data[offset:offset + length]
            offset += length
            fields.append((field_num, "length_delimited", val))
        elif wire_type == 5:  # 32-bit
            val = data[offset:offset + 4]
            offset += 4
            fields.append((field_num, "fixed32", val))
        else:
            # Unsupported wire type or corrupted stream; break early
            break
    return fields


# =============================================================================
# Runtime Extractors
# =============================================================================

class BaseExtractor:
    """Abstract base class for platform-specific telemetry extractors."""
    name: str = "base"

    def is_available(self) -> bool:
        """Return True if the runtime environment or storage exists on disk."""
        raise NotImplementedError

    def find_active_session(self, repo_root: str) -> Optional[Tuple[str, float]]:
        """Return (session_identifier, mtime) if a session exists for repo_root."""
        raise NotImplementedError

    def extract_delta(self, repo_root: str, watermark: dict[str, Any]) -> ExtractionResult:
        """Extract incremental tokens since the last watermark."""
        raise NotImplementedError


class AntigravityExtractor(BaseExtractor):
    """Extractor for Google Antigravity / Gemini IDE SQLite conversation telemetry."""
    name = "antigravity"

    def __init__(self):
        # Check both the standard IDE path and alternate desktop app path
        self.search_dirs = [
            os.path.expanduser("~/.gemini/antigravity-ide/conversations"),
            os.path.expanduser("~/.gemini/antigravity/conversations"),
        ]

    def is_available(self) -> bool:
        return any(os.path.isdir(d) for d in self.search_dirs)

    def find_active_session(self, repo_root: str) -> Optional[Tuple[str, float]]:
        """Find the newest conversation DB linked to repo_root via trajectory_metadata_blob."""
        matching_dbs: list[Tuple[str, float]] = []
        target_marker = f"file://{repo_root}".encode("utf-8")

        for s_dir in self.search_dirs:
            if not os.path.isdir(s_dir):
                continue
            for db_path in glob.glob(os.path.join(s_dir, "*.db")):
                try:
                    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                    cur = conn.cursor()
                    cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id = 'main'")
                    row = cur.fetchone()
                    conn.close()
                    if row and row[0] and target_marker in row[0]:
                        matching_dbs.append((db_path, os.path.getmtime(db_path)))
                except (sqlite3.Error, OSError):
                    continue

        if not matching_dbs:
            return None
        matching_dbs.sort(key=lambda x: x[1], reverse=True)
        return matching_dbs[0]

    def extract_delta(self, repo_root: str, watermark: dict[str, Any]) -> ExtractionResult:
        active = self.find_active_session(repo_root)
        if not active:
            return ExtractionResult(error="antigravity_session_not_found")

        db_path, _ = active
        session_id = os.path.splitext(os.path.basename(db_path))[0]
        last_idx = watermark.get("last_idx", -1)

        # If we switched conversations, reset the index pointer
        if watermark.get("session_id") != session_id:
            last_idx = -1

        delta_in = 0
        delta_out = 0
        delta_thinking = 0
        resolved_model = None
        max_idx = last_idx

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute(
                "SELECT idx, data FROM gen_metadata WHERE idx > ? ORDER BY idx ASC",
                (last_idx,),
            )
            rows = cur.fetchall()
            conn.close()
        except sqlite3.Error as e:
            return ExtractionResult(error=f"antigravity_db_error({type(e).__name__})")

        for idx, blob in rows:
            max_idx = max(max_idx, idx)
            try:
                top_fields = parse_protobuf_fields(blob)
                for fn, wt, val in top_fields:
                    if fn == 1 and wt == "length_delimited":
                        # Field 1 contains turn metadata
                        f1_fields = parse_protobuf_fields(val)
                        for fn1, wt1, val1 in f1_fields:
                            if fn1 == 19 and wt1 == "length_delimited":
                                resolved_model = val1.decode("utf-8", errors="ignore")
                            elif fn1 == 21 and wt1 == "length_delimited" and not resolved_model:
                                resolved_model = val1.decode("utf-8", errors="ignore")
                            elif fn1 == 4 and wt1 == "length_delimited":
                                # Field 4 contains token usage submessage
                                f4_fields = parse_protobuf_fields(val1)
                                varints = {f[0]: f[2] for f in f4_fields if f[1] == "varint"}

                                # Field 2 = prompt tokens (uncached)
                                # Field 5 = cached context tokens
                                # Field 3 = total output tokens
                                # Field 9 = thinking tokens
                                prompt_tokens = varints.get(2, 0)
                                cached_tokens = varints.get(5, 0)
                                output_tokens = varints.get(3, 0)
                                thinking = varints.get(9, 0)

                                delta_in += (prompt_tokens + cached_tokens)
                                delta_out += output_tokens
                                delta_thinking += thinking
            except Exception:
                return ExtractionResult(error="antigravity_schema_drift")

        return ExtractionResult(
            tokens_in=delta_in,
            tokens_out=delta_out,
            thinking_tokens=delta_thinking,
            model=resolved_model or "gemini",
            runtime="antigravity",
            watermark_updates={
                "session_id": session_id,
                "last_idx": max_idx,
                "total_in": watermark.get("total_in", 0) + delta_in,
                "total_out": watermark.get("total_out", 0) + delta_out,
            },
        )


class CopilotExtractor(BaseExtractor):
    """Extractor for GitHub Copilot Chat telemetry stored in VS Code workspaceStorage."""
    name = "copilot"

    def __init__(self):
        # Platform-specific VS Code workspaceStorage locations
        home = os.path.expanduser("~")
        self.search_dirs = [
            os.path.join(home, "Library/Application Support/Code/User/workspaceStorage"),
            os.path.join(home, ".config/Code/User/workspaceStorage"),
            os.path.expandvars("%APPDATA%/Code/User/workspaceStorage"),
        ]

    def is_available(self) -> bool:
        return any(os.path.isdir(d) for d in self.search_dirs)

    def find_active_session(self, repo_root: str) -> Optional[Tuple[str, float]]:
        """Find the newest chat session JSONL inside workspaceStorage matching repo_root."""
        target_folder = f"file://{repo_root}"
        matched_workspace_dir = None

        for s_dir in self.search_dirs:
            if not os.path.isdir(s_dir):
                continue
            for ws_json in glob.glob(os.path.join(s_dir, "*/workspace.json")):
                try:
                    with open(ws_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("folder") == target_folder:
                            matched_workspace_dir = os.path.dirname(ws_json)
                            break
                except (json.JSONDecodeError, OSError):
                    continue
            if matched_workspace_dir:
                break

        if not matched_workspace_dir:
            return None

        chat_sessions_dir = os.path.join(matched_workspace_dir, "chatSessions")
        if not os.path.isdir(chat_sessions_dir):
            return None

        session_files = glob.glob(os.path.join(chat_sessions_dir, "*.jsonl"))
        if not session_files:
            return None

        session_files.sort(key=os.path.getmtime, reverse=True)
        newest = session_files[0]
        return newest, os.path.getmtime(newest)

    def extract_delta(self, repo_root: str, watermark: dict[str, Any]) -> ExtractionResult:
        active = self.find_active_session(repo_root)
        if not active:
            return ExtractionResult(error="copilot_session_not_found")

        session_path, _ = active
        session_id = os.path.splitext(os.path.basename(session_path))[0]
        last_offset = watermark.get("offset", 0)

        if watermark.get("session_id") != session_id:
            last_offset = 0

        delta_in = 0
        delta_out = 0
        delta_thinking = 0
        resolved_model = None

        try:
            with open(session_path, "r", encoding="utf-8") as f:
                f.seek(last_offset)
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        # Recursive search for token usage metrics
                        def scan(obj: Any):
                            nonlocal delta_in, delta_out, delta_thinking, resolved_model
                            if isinstance(obj, dict):
                                if "promptTokens" in obj and isinstance(obj["promptTokens"], int):
                                    delta_in += obj["promptTokens"]
                                if "outputTokens" in obj and isinstance(obj["outputTokens"], int):
                                    delta_out += obj["outputTokens"]
                                elif "completionTokens" in obj and isinstance(obj["completionTokens"], int):
                                    delta_out += obj["completionTokens"]
                                if "thinking" in obj and isinstance(obj["thinking"], dict):
                                    t = obj["thinking"].get("tokens", 0)
                                    if isinstance(t, int):
                                        delta_thinking += t
                                if "resolvedModel" in obj and isinstance(obj["resolvedModel"], str):
                                    resolved_model = obj["resolvedModel"]
                                elif "modelId" in obj and isinstance(obj["modelId"], str) and not resolved_model:
                                    resolved_model = obj["modelId"]

                                for v in obj.values():
                                    scan(v)
                            elif isinstance(obj, list):
                                for item in obj:
                                    scan(item)

                        scan(record)
                    except json.JSONDecodeError:
                        continue
                new_offset = f.tell()
        except OSError as e:
            return ExtractionResult(error=f"copilot_io_error({type(e).__name__})")

        return ExtractionResult(
            tokens_in=delta_in,
            tokens_out=delta_out,
            thinking_tokens=delta_thinking,
            model=resolved_model or "copilot",
            runtime="copilot",
            watermark_updates={
                "session_id": session_id,
                "offset": new_offset,
                "total_in": watermark.get("total_in", 0) + delta_in,
                "total_out": watermark.get("total_out", 0) + delta_out,
            },
        )


class ClaudeExtractor(BaseExtractor):
    """Extractor for Anthropic Claude Code session telemetry (~/.claude/projects/)."""
    name = "claude-code"

    def is_available(self) -> bool:
        return os.path.isdir(os.path.expanduser("~/.claude/projects"))

    def find_active_session(self, repo_root: str) -> Optional[Tuple[str, float]]:
        mangled = repo_root.replace("/", "-")
        claude_dir = os.path.expanduser(f"~/.claude/projects/{mangled}")
        if not os.path.isdir(claude_dir):
            return None

        session_dirs = [
            d for d in glob.glob(os.path.join(claude_dir, "*/")) if os.path.isdir(d)
        ]
        if not session_dirs:
            return None
        session_dirs.sort(key=os.path.getmtime, reverse=True)
        newest = session_dirs[0]
        return newest, os.path.getmtime(newest)

    def extract_delta(self, repo_root: str, watermark: dict[str, Any]) -> ExtractionResult:
        active = self.find_active_session(repo_root)
        if not active:
            return ExtractionResult(error="claude_session_not_found")

        session_dir, _ = active
        session_id = os.path.basename(session_dir.rstrip("/"))

        # Collect all session JSONL files (main session + subagents)
        jsonl_files: list[str] = []
        subagent_dir = os.path.join(session_dir, "subagents")
        if os.path.isdir(subagent_dir):
            jsonl_files.extend(glob.glob(os.path.join(subagent_dir, "*.jsonl")))

        main_jsonl = session_dir.rstrip("/") + ".jsonl"
        if os.path.exists(main_jsonl):
            jsonl_files.append(main_jsonl)

        # Fallback to files directly inside session_dir
        jsonl_files.extend(glob.glob(os.path.join(session_dir, "*.jsonl")))
        jsonl_files = sorted(set(jsonl_files))

        if not jsonl_files:
            return ExtractionResult(error="claude_no_jsonl_found")

        file_offsets = watermark.get("file_offsets", {})
        if watermark.get("session_id") != session_id:
            file_offsets = {}

        delta_in = 0
        delta_out = 0
        new_offsets = dict(file_offsets)

        for fpath in jsonl_files:
            offset = file_offsets.get(fpath, 0)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    f.seek(offset)
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line)
                            usage = entry.get("message", {}).get("usage", {})
                            if usage:
                                delta_in += (
                                    usage.get("input_tokens", 0)
                                    + usage.get("cache_creation_input_tokens", 0)
                                    + usage.get("cache_read_input_tokens", 0)
                                )
                                delta_out += usage.get("output_tokens", 0)
                        except (json.JSONDecodeError, AttributeError):
                            continue
                    new_offsets[fpath] = f.tell()
            except OSError:
                continue

        return ExtractionResult(
            tokens_in=delta_in,
            tokens_out=delta_out,
            model="claude",
            runtime="claude-code",
            watermark_updates={
                "session_id": session_id,
                "file_offsets": new_offsets,
                "total_in": watermark.get("total_in", 0) + delta_in,
                "total_out": watermark.get("total_out", 0) + delta_out,
            },
        )


class CodexExtractor(BaseExtractor):
    """Fallback extractor for OpenAI Codex / API run steps."""
    name = "codex"

    def is_available(self) -> bool:
        return os.path.isdir(os.path.expanduser("~/.codex"))

    def find_active_session(self, repo_root: str) -> Optional[Tuple[str, float]]:
        return None

    def extract_delta(self, repo_root: str, watermark: dict[str, Any]) -> ExtractionResult:
        return ExtractionResult(error="codex_extractor_not_configured")


# =============================================================================
# Commit Message Injection & Dispatcher
# =============================================================================

EXTRACTORS: dict[str, BaseExtractor] = {
    "antigravity": AntigravityExtractor(),
    "gemini": AntigravityExtractor(),
    "copilot": CopilotExtractor(),
    "github": CopilotExtractor(),
    "claude-code": ClaudeExtractor(),
    "claude": ClaudeExtractor(),
    "codex": CodexExtractor(),
    "openai": CodexExtractor(),
}


def select_extractor(declared_tool: Optional[str], repo_root: str) -> BaseExtractor:
    """Select the appropriate extractor based on declared tool or freshest session."""
    if declared_tool:
        norm = declared_tool.strip().lower()
        if norm in EXTRACTORS:
            return EXTRACTORS[norm]

    # Auto-detect: find the runtime whose matching session has the freshest mtime
    candidates: list[Tuple[BaseExtractor, float]] = []
    unique_extractors = {
        AntigravityExtractor.name: AntigravityExtractor(),
        CopilotExtractor.name: CopilotExtractor(),
        ClaudeExtractor.name: ClaudeExtractor(),
    }

    for ext in unique_extractors.values():
        if ext.is_available():
            active = ext.find_active_session(repo_root)
            if active:
                candidates.append((ext, active[1]))

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    # Default fallback to Antigravity then Claude
    return AntigravityExtractor() if AntigravityExtractor().is_available() else ClaudeExtractor()


def update_commit_message(msg_file: str, token_str: str) -> bool:
    """Inject or replace token_str on the Agent-Session line in msg_file."""
    try:
        with open(msg_file, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return False

    if "Agent-Session:" not in content:
        # Human commit without Agent-Session trailer; leave untouched
        return False

    lines = content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("Agent-Session:"):
            if "tokens=" in line:
                lines[i] = re.sub(r"tokens=\S+", token_str, line)
            else:
                lines[i] = line.rstrip() + " " + token_str
            updated = True
            break

    if updated:
        try:
            with open(msg_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except OSError:
            pass
    return False


def main() -> None:
    """Main git hook entry point."""
    if len(sys.argv) < 2:
        sys.exit(0)

    msg_file = sys.argv[1]
    commit_source = sys.argv[2] if len(sys.argv) > 2 else ""

    # Skip merge and squash commits
    if commit_source in ("merge", "squash"):
        sys.exit(0)

    try:
        with open(msg_file, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        sys.exit(0)

    if "Agent-Session:" not in content:
        # Human commit; do nothing
        sys.exit(0)

    repo_root = get_git_repo_root()
    if not repo_root:
        sys.exit(0)

    # Extract declared tool container from Agent-Session line
    declared_tool = None
    tool_match = re.search(r"tool=([a-zA-Z0-9_\-]+)", content)
    if tool_match:
        declared_tool = tool_match.group(1)

    extractor = select_extractor(declared_tool, repo_root)
    watermark_file = get_watermark_path(repo_root, extractor.name)
    current_watermark = read_watermark(watermark_file)

    result = extractor.extract_delta(repo_root, current_watermark)

    if result.error:
        # Emit warning to stderr and record transparent error trailer in commit message
        sys.stderr.write(f"[prepare-commit-msg] Warning: {result.error}\n")
        update_commit_message(msg_file, f"tokens=error({result.error})")
        sys.exit(0)

    # Annotate tokens if there are consumed tokens to report
    if result.tokens_in > 0 or result.tokens_out > 0:
        token_str = f"tokens={format_tokens(result.tokens_in)}/{format_tokens(result.tokens_out)}"
        update_commit_message(msg_file, token_str)

        # Persist watermark updates for next commit
        if result.watermark_updates:
            current_watermark.update(result.watermark_updates)
            write_watermark(watermark_file, current_watermark)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Failsafe: never block git commit on unexpected exceptions
        sys.stderr.write(f"[prepare-commit-msg] Unexpected hook error: {exc}\n")
        sys.exit(0)
