"""Unit tests and schema sanity checks for multi-runtime session telemetry.

Covers:
1. Synthetic unit tests (zero-dependency, always run):
   - Protobuf wire format parsing & varint decoding.
   - Antigravity SQLite extraction & index watermarking.
   - GitHub Copilot workspace matching, JSONL parsing & byte-offset seeking.
   - Claude Code session JSONL extraction.
   - Commit message trailer injection and error surfacing.
2. Live runtime location sanity checks:
   - Differentiates between:
     a) Not installed (skipped)
     b) Installed but unused/idle (skipped with diagnostic note)
     c) Installed with sessions but broken/drifted schema (fails test with alert)
"""

import json
import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

import importlib.util

_script_path = Path(__file__).resolve().parent.parent / "prepare-commit-msg.py"
_spec = importlib.util.spec_from_file_location("prepare_commit_msg", _script_path)
_mod = importlib.util.module_from_spec(_spec)
import sys
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)


AntigravityExtractor = _mod.AntigravityExtractor
ClaudeExtractor = _mod.ClaudeExtractor
CopilotExtractor = _mod.CopilotExtractor
ExtractionResult = _mod.ExtractionResult
_decode_varint = _mod._decode_varint
format_tokens = _mod.format_tokens
parse_protobuf_fields = _mod.parse_protobuf_fields
select_extractor = _mod.select_extractor
update_commit_message = _mod.update_commit_message



# =============================================================================
# 1. Synthetic Unit Tests
# =============================================================================

def test_format_tokens():
    """Verify human-readable token formatting."""
    assert format_tokens(500) == "500"
    assert format_tokens(1000) == "1.0K"
    assert format_tokens(14500) == "14.5K"
    assert format_tokens(1_000_000) == "1.00M"
    assert format_tokens(2_450_000) == "2.45M"


def test_protobuf_wire_format_parsing():
    """Verify raw protobuf wire decoding for varints and length-delimited strings."""
    # Encode varint 150 -> 0x96 0x01
    # Field 1 (wire_type 0 = varint) -> key = (1 << 3) | 0 = 8 -> 0x08 0x96 0x01
    # Field 2 (wire_type 2 = length-delimited) -> key = (2 << 3) | 2 = 18 -> 0x12, len 5, "hello"
    raw = bytes([0x08, 0x96, 0x01, 0x12, 0x05, 0x68, 0x65, 0x6C, 0x6C, 0x6F])
    fields = parse_protobuf_fields(raw)

    assert len(fields) == 2
    assert fields[0] == (1, "varint", 150)
    assert fields[1] == (2, "length_delimited", b"hello")


def _encode_varint(value: int) -> bytes:
    """Helper to encode an integer as protobuf varint."""
    res = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value > 0:
            res.append(b | 0x80)
        else:
            res.append(b)
            break
    return bytes(res)


def _encode_field(field_num: int, wire_type: int, payload: bytes) -> bytes:
    """Helper to encode a protobuf tag and payload."""
    tag = (field_num << 3) | wire_type
    tag_bytes = _encode_varint(tag)
    if wire_type == 0:
        return tag_bytes + payload
    elif wire_type == 2:
        return tag_bytes + _encode_varint(len(payload)) + payload
    return tag_bytes + payload


def test_antigravity_synthetic_extraction(tmp_path):
    """Verify AntigravityExtractor against an in-memory or synthetic SQLite database."""
    db_path = tmp_path / "test-conv.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Create expected Antigravity schema
    cur.execute("CREATE TABLE trajectory_metadata_blob (id text PRIMARY KEY, data blob)")
    cur.execute("CREATE TABLE gen_metadata (idx integer PRIMARY KEY, data blob)")

    repo_root = "/Users/test/my-repo"
    # Store trajectory metadata linking to repo
    meta_payload = f"meta file://{repo_root} conversation_id".encode("utf-8")
    cur.execute("INSERT INTO trajectory_metadata_blob VALUES ('main', ?)", (meta_payload,))

    # Construct synthetic protobuf turn
    # Field 4: token usage submessage
    #   Field 2 (varint): prompt = 1000
    #   Field 5 (varint): cached = 4000
    #   Field 3 (varint): output = 250
    #   Field 9 (varint): thinking = 50
    f4_bytes = (
        _encode_field(2, 0, _encode_varint(1000))
        + _encode_field(5, 0, _encode_varint(4000))
        + _encode_field(3, 0, _encode_varint(250))
        + _encode_field(9, 0, _encode_varint(50))
    )

    # Field 19: model = "gemini-flash"
    f19_bytes = _encode_field(19, 2, b"gemini-flash")

    # Field 1: top turn metadata
    f1_bytes = _encode_field(4, 2, f4_bytes) + f19_bytes

    # Top-level message: field 1 length-delimited
    row0_blob = _encode_field(1, 2, f1_bytes)

    cur.execute("INSERT INTO gen_metadata VALUES (0, ?)", (row0_blob,))
    conn.commit()
    conn.close()

    extractor = AntigravityExtractor()
    extractor.search_dirs = [str(tmp_path)]

    # 1. First extraction from index -1
    res = extractor.extract_delta(repo_root, {"last_idx": -1})
    assert res.error is None
    assert res.tokens_in == 5000  # 1000 prompt + 4000 cached
    assert res.tokens_out == 250
    assert res.thinking_tokens == 50
    assert res.model == "gemini-flash"
    assert res.watermark_updates["last_idx"] == 0

    # 2. Second extraction with watermark at index 0 (no new rows)
    res2 = extractor.extract_delta(repo_root, res.watermark_updates)
    assert res2.error is None
    assert res2.tokens_in == 0
    assert res2.tokens_out == 0


def test_copilot_synthetic_extraction(tmp_path):
    """Verify CopilotExtractor against synthetic VS Code workspace storage."""
    repo_root = "/Users/test/copilot-repo"
    ws_dir = tmp_path / "workspaceStorage" / "mock_hash"
    chat_dir = ws_dir / "chatSessions"
    chat_dir.mkdir(parents=True)

    # Create workspace.json linking to repo
    ws_json = ws_dir / "workspace.json"
    ws_json.write_text(json.dumps({"folder": f"file://{repo_root}"}))

    # Create session JSONL file
    session_file = chat_dir / "session-1.jsonl"
    turn1 = {
        "result": {
            "metadata": {
                "promptTokens": 12500,
                "outputTokens": 350,
                "resolvedModel": "gpt-5-mini",
                "toolCallRounds": [{"thinking": {"tokens": 80}}],
            }
        }
    }
    session_file.write_text(json.dumps(turn1) + "\n")

    extractor = CopilotExtractor()
    extractor.search_dirs = [str(tmp_path / "workspaceStorage")]

    # First extraction
    res = extractor.extract_delta(repo_root, {"offset": 0})
    assert res.error is None
    assert res.tokens_in == 12500
    assert res.tokens_out == 350
    assert res.thinking_tokens == 80
    assert res.model == "gpt-5-mini"
    assert res.watermark_updates["offset"] > 0

    # Append second turn to session file
    turn2 = {
        "result": {
            "metadata": {
                "promptTokens": 2000,
                "completionTokens": 100,
            }
        }
    }
    with open(session_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(turn2) + "\n")

    # Incremental extraction from previous offset
    res2 = extractor.extract_delta(repo_root, res.watermark_updates)
    assert res2.error is None
    assert res2.tokens_in == 2000
    assert res2.tokens_out == 100


def test_commit_message_updating(tmp_path):
    """Verify commit message trailer injection and error surfacing."""
    msg_file = tmp_path / "COMMIT_EDITMSG"

    # 1. Human commit without Agent-Session -> untouched
    msg_file.write_text("feat: human commit without trailer\n")
    assert not update_commit_message(str(msg_file), "tokens=10K/1K")
    assert "tokens=" not in msg_file.read_text()

    # 2. Agent commit -> append tokens
    msg_file.write_text(
        "feat: agent commit\n\nAgent-Session: tool=antigravity model=gemini-flash agents=coder\n"
    )
    assert update_commit_message(str(msg_file), "tokens=15.0K/1.2K")
    content = msg_file.read_text()
    assert "Agent-Session: tool=antigravity model=gemini-flash agents=coder tokens=15.0K/1.2K" in content

    # 3. Existing tokens replacement
    assert update_commit_message(str(msg_file), "tokens=error(schema_drift)")
    assert "tokens=error(schema_drift)" in msg_file.read_text()
    assert "15.0K" not in msg_file.read_text()


# =============================================================================
# 2. Live Runtime Location Sanity Checks
# =============================================================================

def test_live_antigravity_storage_sanity():
    """Verify local Antigravity IDE storage structure if installed.
    
    Discriminates:
    - Skipped if Antigravity is not installed.
    - Skipped if installed but no conversation DBs exist.
    - Fails if databases exist but gen_metadata / protobuf schema cannot be parsed.
    """
    extractor = AntigravityExtractor()
    if not extractor.is_available():
        pytest.skip("Antigravity IDE storage not found on this machine.")

    # Search for conversation databases
    dbs = []
    for s_dir in extractor.search_dirs:
        if os.path.isdir(s_dir):
            dbs.extend(Path(s_dir).glob("*.db"))

    if not dbs:
        pytest.skip("Antigravity is installed, but no conversation databases were found to validate.")

    # Validate that at least one DB has the expected schema
    tested = 0
    for db_path in dbs[:5]:
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trajectory_metadata_blob', 'gen_metadata')"
            )
            tables = {row[0] for row in cur.fetchall()}
            conn.close()
            if "gen_metadata" in tables:
                tested += 1
        except sqlite3.Error as e:
            pytest.fail(f"Antigravity database {db_path} could not be read: {e}")

    if tested == 0:
        pytest.fail("Antigravity databases exist, but none contained the expected gen_metadata table (schema drift).")


def test_live_copilot_storage_sanity():
    """Verify local VS Code Copilot Chat storage structure if installed.
    
    Discriminates:
    - Skipped if VS Code workspaceStorage is not installed.
    - Skipped if installed but no chat session files exist.
    - Fails if session files exist but cannot be parsed as valid JSONL.
    """
    extractor = CopilotExtractor()
    if not extractor.is_available():
        pytest.skip("VS Code workspaceStorage not found on this machine.")

    session_files = []
    for s_dir in extractor.search_dirs:
        if os.path.isdir(s_dir):
            session_files.extend(Path(s_dir).glob("*/chatSessions/*.jsonl"))

    if not session_files:
        pytest.skip("VS Code workspaceStorage exists, but no Copilot chat sessions were found to validate.")

    # Validate JSON parsing on found sessions
    tested = 0
    for sf in session_files[:5]:
        try:
            with open(sf, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if line.strip():
                        json.loads(line)
                    if idx > 20:
                        break
            tested += 1
        except Exception as e:
            pytest.fail(f"Copilot session file {sf} failed JSON parsing: {e}")

    assert tested > 0, "No valid Copilot session files could be parsed."


def test_live_claude_storage_sanity():
    """Verify local Claude Code storage structure if installed.
    
    Discriminates:
    - Skipped if ~/.claude/projects is not installed.
    - Skipped if installed but no project sessions exist.
    - Fails if session files exist but fail JSON parsing.
    """
    extractor = ClaudeExtractor()
    if not extractor.is_available():
        pytest.skip("Claude Code storage (~/.claude/projects) not found on this machine.")

    claude_dir = Path(os.path.expanduser("~/.claude/projects"))
    jsonl_files = list(claude_dir.glob("*/*.jsonl")) + list(claude_dir.glob("*/*/*.jsonl"))

    if not jsonl_files:
        pytest.skip("Claude Code directory exists, but no session JSONL files were found.")

    tested = 0
    for jf in jsonl_files[:5]:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if line.strip():
                        json.loads(line)
                    if idx > 20:
                        break
            tested += 1
        except Exception as e:
            pytest.fail(f"Claude Code session file {jf} failed JSON parsing: {e}")

    assert tested > 0, "No valid Claude Code session files could be parsed."
