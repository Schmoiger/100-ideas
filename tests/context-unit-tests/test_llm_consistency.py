"""
LLM-based consistency checks for agent documentation.

Runs a single LLM call to verify semantic consistency across docs.
Designed to be fast enough for PR checks (~10-15 seconds).
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

# Skip if no API key configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


def collect_docs() -> dict[str, str]:
    """Collect all documentation files into a single context."""
    docs = {}
    base = Path(__file__).parent.parent.parent / "context"

    # Key files to check for consistency
    patterns = [
        "agents/*.md",
        "standards/*.md",
        "rules/*.mdc",
        "README.md",
    ]

    for pattern in patterns:
        for path in base.glob(pattern):
            if path.is_file():
                rel_path = path.relative_to(base)
                # Truncate large files to stay within context limits
                content = path.read_text()
                if len(content) > 10000:
                    content = content[:10000] + "\n... [truncated]"
                docs[str(rel_path)] = content

    return docs


def build_consistency_prompt(docs: dict[str, str]) -> str:
    """Build prompt for consistency check."""
    docs_context = "\n\n".join(
        f"=== {path} ===\n{content}"
        for path, content in sorted(docs.items())
    )

    return f"""You are a documentation auditor. Check these agent documentation files for consistency issues.

DOCUMENTATION FILES:
{docs_context}

CHECK FOR THESE SPECIFIC ISSUES:

1. **File Reference Errors**: Any `./path/to/file` references that point to files not in this doc set
2. **Agent Name Mismatches**: Agent names in CLAUDE.md that don't match actual agent file names
3. **Domain Inconsistencies**: Domains in agent-standards.md that don't match workflow definitions or CLAUDE.md
4. **Artifact Path Conflicts**: Different docs claiming different output paths for the same agent
5. **Standards Contradictions**: Rules in one doc that contradict rules in another
6. **Missing Cross-References**: Agents mentioned but not defined, or standards referenced but not present

OUTPUT FORMAT (JSON only, no other text):
{{
  "status": "pass" | "fail",
  "issues": [
    {{
      "type": "file_reference" | "agent_mismatch" | "domain_inconsistency" | "path_conflict" | "contradiction" | "missing_reference",
      "severity": "error" | "warning",
      "location": "file.md",
      "description": "Brief description of the issue",
      "suggestion": "How to fix it"
    }}
  ],
  "summary": "One sentence summary"
}}

If no issues found, return {{"status": "pass", "issues": [], "summary": "All documentation is consistent."}}

Be strict. Only report actual inconsistencies, not style preferences."""


def call_llm(prompt: str) -> dict[str, Any]:
    """Call Anthropic API with the consistency check prompt."""
    try:
        import anthropic
    except ImportError:
        pytest.skip("anthropic package not installed")

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",  # Fast and cheap for CI
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract JSON from response
    text = response.content[0].text.strip()

    # Handle markdown code blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


class TestLLMConsistency:
    """LLM-based consistency tests."""

    @pytest.fixture(scope="class")
    def consistency_result(self) -> dict[str, Any]:
        """Run consistency check once and cache result."""
        docs = collect_docs()
        prompt = build_consistency_prompt(docs)
        return call_llm(prompt)

    def test_no_errors(self, consistency_result: dict[str, Any]):
        """Fail if any error-severity issues found."""
        errors = [
            issue for issue in consistency_result.get("issues", [])
            if issue.get("severity") == "error"
        ]

        if errors:
            error_report = "\n".join(
                f"  - [{e['type']}] {e['location']}: {e['description']}"
                for e in errors
            )
            pytest.fail(f"Documentation consistency errors:\n{error_report}")

    def test_status_pass(self, consistency_result: dict[str, Any]):
        """Check overall status."""
        if consistency_result.get("status") == "fail":
            # Only fail on errors, warnings are informational
            errors = [
                i for i in consistency_result.get("issues", [])
                if i.get("severity") == "error"
            ]
            if errors:
                pytest.fail(f"Consistency check failed: {consistency_result.get('summary')}")

    def test_print_warnings(self, consistency_result: dict[str, Any], capsys):
        """Print warnings for visibility (doesn't fail)."""
        warnings = [
            issue for issue in consistency_result.get("issues", [])
            if issue.get("severity") == "warning"
        ]

        if warnings:
            print("\nConsistency warnings (non-blocking):")
            for w in warnings:
                print(f"  - [{w['type']}] {w['location']}: {w['description']}")
                if w.get("suggestion"):
                    print(f"    Suggestion: {w['suggestion']}")


# Allow running directly for debugging
if __name__ == "__main__":
    docs = collect_docs()
    print(f"Collected {len(docs)} documentation files")

    prompt = build_consistency_prompt(docs)
    print(f"Prompt size: {len(prompt)} chars")

    if os.environ.get("ANTHROPIC_API_KEY"):
        result = call_llm(prompt)
        print(json.dumps(result, indent=2))
    else:
        print("Set ANTHROPIC_API_KEY to run LLM check")
