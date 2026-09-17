"""
Pytest configuration for documentation tests.
"""

import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "llm: tests that require LLM API calls (may be slow/costly)"
    )
