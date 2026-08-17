"""Render rich-click help as YAML."""

from __future__ import annotations

import json

import click
import yaml
from rich_click.help_json import command_schema


def render(command: click.Command, ctx: click.Context) -> str:
    """Return the complete command tree as YAML."""
    schema = command_schema(command, ctx, recursive=True)
    serializable = json.loads(json.dumps(schema, default=str))
    return yaml.safe_dump(serializable, sort_keys=False, default_flow_style=False, allow_unicode=True)
