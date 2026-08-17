"""Render rich-click help as a Carapace command specification."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

import click
import yaml
from rich.errors import MarkupError
from rich.text import Text
from rich_click.help_json import command_schema


SCHEMA_DIRECTIVE = "# yaml-language-server: $schema=https://carapace.sh/schemas/command.json"


def _flag_name(opts: Sequence[str]) -> str:
    """Return the bare flag name that Carapace uses for completion."""
    long_opts = [opt for opt in opts if opt.startswith("--")]
    return (long_opts[0] if long_opts else opts[0]).lstrip("-")


def _plain_text(value: str | None) -> str | None:
    """Return help text without Rich markup."""
    if not value:
        return value
    if "[" not in value:
        return value.strip()
    try:
        return Text.from_markup(value).plain.strip()
    except MarkupError:
        return value.strip()


def _parameters(
    params: list[dict[str, Any]], raw_params: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Convert rich-click parameters to Carapace flags, completion, and documentation."""
    flags: dict[str, Any] = {}
    flag_completion: dict[str, Any] = {}
    positional_completion: list[list[Any]] = []
    positional_docs: list[str] = []
    completion: dict[str, Any] = {}
    documentation: dict[str, Any] = {}

    for param, raw_param in zip(params, raw_params, strict=True):
        kind = param.get("kind")
        choices = list(param.get("choices") or [])
        help_text = str(param.get("help") or "")
        if kind == "option":
            opts = list(param.get("opts") or [])
            if not opts:
                continue
            takes_value = not param.get("is_flag") and not param.get("count")
            key = ", ".join(str(opt) for opt in opts)
            if takes_value:
                key += "?" if raw_param.get("flag_value") is not None else "="
            if param.get("multiple"):
                key += "*"
            nargs = param.get("nargs") or 1
            if takes_value and isinstance(nargs, int) and nargs > 1:
                flags[key] = {"description": help_text, "nargs": nargs}
            else:
                flags[key] = help_text
            for secondary in param.get("secondary_opts") or []:
                flags[str(secondary)] = help_text
            if choices:
                flag_completion[_flag_name(opts)] = choices
        elif kind == "argument":
            nargs = param.get("nargs")
            if nargs == -1:
                if choices:
                    completion["positionalany"] = choices
                if help_text:
                    documentation["positionalany"] = help_text
                continue
            slots = nargs if isinstance(nargs, int) and nargs > 0 else 1
            positional_completion.extend([choices] * slots)
            positional_docs.extend([help_text] * slots)

    if flag_completion:
        completion["flag"] = flag_completion
    if any(positional_completion):
        completion["positional"] = positional_completion
    if any(positional_docs):
        documentation["positional"] = positional_docs
    return flags, completion, documentation


def _child_contexts(command: click.Command, ctx: click.Context) -> Iterator[tuple[str, click.Command, click.Context]]:
    """Yield each subcommand with a context suitable for help rendering."""
    list_commands = getattr(command, "list_commands", None)
    get_command = getattr(command, "get_command", None)
    if list_commands is None or get_command is None:
        return
    for name in list_commands(ctx):
        child = get_command(ctx, name)
        if child is None:
            continue
        try:
            child_ctx = child.make_context(name, [], parent=ctx, resilient_parsing=True)
        except click.ClickException:
            continue
        yield name, child, child_ctx


def _command(schema: dict[str, Any], command: click.Command, ctx: click.Context) -> dict[str, Any]:
    """Convert one recursive rich-click schema node to a Carapace command."""
    result: dict[str, Any] = {"name": schema.get("name") or ""}
    description = _plain_text(command.get_short_help_str(limit=120))
    if description:
        result["description"] = description
    if schema.get("aliases"):
        result["aliases"] = list(schema["aliases"])
    if schema.get("hidden"):
        result["hidden"] = True
    if "subcommands" in schema:
        result["parsing"] = "non-interspersed"

    raw_params = [param.to_info_dict() for param in command.get_params(ctx)]
    flags, completion, documentation = _parameters(schema.get("params") or [], raw_params)
    if flags:
        result["flags"] = flags
    if completion:
        result["completion"] = completion
    if documentation:
        result["documentation"] = documentation
    if schema.get("examples"):
        result["examples"] = {
            str(example["command"]): str(example.get("description") or "") for example in schema["examples"]
        }
    child_schemas = schema.get("subcommands") or {}
    commands = [
        _command(child_schemas[name], child, child_ctx)
        for name, child, child_ctx in _child_contexts(command, ctx)
        if name in child_schemas
    ]
    if commands:
        result["commands"] = commands
    return result


def render(command: click.Command, ctx: click.Context) -> str:
    """Return the complete command tree as a Carapace YAML specification."""
    schema = command_schema(command, ctx, recursive=True)
    data = _command(schema, command, ctx)
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return f"{SCHEMA_DIRECTIVE}\n{body}"
