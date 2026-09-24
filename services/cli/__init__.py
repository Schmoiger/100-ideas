"""System-wide CLI dispatcher for the 100-Ideas Agentic Publishing System.

This package hosts the canonical argument parser and command dispatcher.
Each subcommand lives in its own module under ``services.cli.commands``,
inverting the historical dependency from ``services.ingestion.cli`` (which
imported all downstream services) into a clean top-level dispatcher that
sits *above* all domain packages.
"""
