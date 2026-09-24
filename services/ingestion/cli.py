"""Legacy CLI shim for ``services.ingestion.cli``.

.. deprecated::
    The canonical CLI entry point has moved to ``services.cli.main``.
    This module re-exports everything from that package so that existing
    test imports continue to work without modification.

    All new code should import from ``services.cli`` directly.

``pyproject.toml`` entry point::

    ideas = "services.cli.main:main"

This file is intentionally kept thin — do not add new command logic here.
"""

from __future__ import annotations

# Re-export shared helpers that tests import directly from this module.
from services.cli._shared import (  # noqa: F401
    confirm_batch_execution,
    get_default_paths,
    get_inbox_archive_path,
    get_repo_root,
    resolve_ideas_to_process,
)

# Re-export enrich/typeset/publishing handlers
from services.cli.commands.enrich import handle_enrich_command  # noqa: F401

# Re-export next-idea-number helper that lives in commands.ingest
from services.cli.commands.ingest import (  # noqa: F401
    get_next_idea_number,
    handle_add_command,
    handle_catalog_command,
    handle_inbox_command,
    handle_sync_command,
)
from services.cli.commands.publishing import (  # noqa: F401
    handle_blog_command,
    handle_pipeline_command,
    handle_social_command,
)
from services.cli.commands.review import (  # noqa: F401
    handle_mark_edited_command,
    handle_review_command,
)
from services.cli.commands.revise import handle_revise_command  # noqa: F401
from services.cli.commands.typeset import (  # noqa: F401
    handle_draft_command,
    handle_typeset_command,
)

# Re-export the parser and main entry point so that
# ``from services.ingestion.cli import main`` and ``build_parser`` continue
# to resolve correctly in existing tests.
from services.cli.main import build_parser, main  # noqa: F401
