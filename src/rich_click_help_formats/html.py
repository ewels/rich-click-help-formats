"""Render rich-click help as a standalone HTML document."""

from __future__ import annotations

from base64 import urlsafe_b64encode
from html import escape
from typing import Any

import click
from rich_click.help_json import command_schema

_STYLES = """
:root { color-scheme: light dark; font-family: system-ui, sans-serif; line-height: 1.5; }
body { margin: 0 auto; max-width: 72rem; padding: 2rem; }
code { background: color-mix(in srgb, currentColor 8%, transparent); padding: .1rem .3rem; }
section.command { border-top: 1px solid color-mix(in srgb, currentColor 25%, transparent); margin-top: 2rem; }
table { border-collapse: collapse; display: block; max-width: 100%; overflow-x: auto; width: max-content; }
th, td { border: 1px solid color-mix(in srgb, currentColor 25%, transparent); padding: .4rem .6rem; text-align: left; }
th { background: color-mix(in srgb, currentColor 8%, transparent); }
""".strip()


def _slug(path: str) -> str:
    """Return a stable, collision-free HTML identifier for a command path."""
    encoded = urlsafe_b64encode(path.encode()).decode().rstrip("=")
    return f"command-{encoded or 'root'}"


def _code(value: Any) -> str:
    """Return an escaped value in a code element."""
    return f"<code>{escape(str(value))}</code>"


def _type_label(param: dict[str, Any]) -> str:
    """Return a readable parameter type."""
    if param.get("count"):
        label = "counter"
    elif param.get("is_flag"):
        label = "flag"
    elif param.get("choices"):
        label = "choice: " + " / ".join(str(choice) for choice in param["choices"])
    else:
        label = str(param.get("type") or "text")
    details = []
    if param.get("multiple"):
        details.append("repeatable")
    if param.get("nargs") == -1:
        details.append("variadic")
    elif isinstance(param.get("nargs"), int) and param["nargs"] > 1:
        details.append(f"{param['nargs']} values")
    return f"{label} ({', '.join(details)})" if details else label


def _parameter_name(param: dict[str, Any]) -> str:
    """Return the visible name of one parameter."""
    if param.get("kind") == "option":
        names = [*(param.get("opts") or []), *(param.get("secondary_opts") or [])]
        return ", ".join(str(name) for name in names)
    return str(param.get("name") or "")


def _parameter_row(param: dict[str, Any]) -> str:
    """Render one parameter table row."""
    required = "yes" if param.get("required") else ""
    default = _code(param["default"]) if "default" in param else ""
    envvar = param.get("envvar") or ""
    if isinstance(envvar, list):
        envvar = ", ".join(str(item) for item in envvar)
    return (
        "<tr>"
        f"<td>{_code(_parameter_name(param))}</td>"
        f"<td>{escape(_type_label(param))}</td>"
        f"<td>{required}</td>"
        f"<td>{default}</td>"
        f"<td>{escape(str(envvar))}</td>"
        f"<td>{escape(str(param.get('help') or ''))}</td>"
        "</tr>"
    )


def _parameter_table(params: list[dict[str, Any]], kind: str) -> str:
    """Render the arguments or options table."""
    rows = [param for param in params if param.get("kind") == kind and not param.get("hidden")]
    if not rows:
        return ""
    heading = "Arguments" if kind == "argument" else "Options"
    body = "".join(_parameter_row(param) for param in rows)
    return (
        f"<h3>{heading}</h3>"
        f'<table class="{kind}s"><thead><tr><th>{heading[:-1]}</th><th>Type</th><th>Required</th>'
        "<th>Default</th><th>Environment</th><th>Description</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _help_paragraphs(value: Any) -> str:
    """Render plain help text as HTML paragraphs."""
    paragraphs = [part.strip() for part in str(value or "").split("\n\n") if part.strip()]
    return "".join(f"<p>{escape(paragraph).replace(chr(10), '<br>')}</p>" for paragraph in paragraphs)


def _subcommand_link(name: str, schema: dict[str, Any]) -> str:
    """Render one subcommand index item."""
    path = str(schema.get("path") or name)
    summary = schema.get("short_help")
    description = f": {escape(str(summary))}" if summary else ""
    return f'<li><a href="#{escape(_slug(path))}">{_code(name)}</a>{description}</li>'


def _command_section(schema: dict[str, Any], level: int = 1) -> str:
    """Render one command and all descendants."""
    path = str(schema.get("path") or schema.get("name") or "")
    heading_level = min(level, 6)
    parts = [
        f'<section class="command" id="{escape(_slug(path))}">',
        f"<h{heading_level}>{_code(path)}</h{heading_level}>",
        _help_paragraphs(schema.get("help")),
    ]
    if schema.get("aliases"):
        aliases = ", ".join(_code(alias) for alias in schema["aliases"])
        parts.append(f"<p><strong>Aliases:</strong> {aliases}</p>")
    if schema.get("usage"):
        parts.append(f"<p><strong>Usage:</strong> {_code(schema['usage'])}</p>")
    parts.append(_parameter_table(schema.get("params") or [], "argument"))
    parts.append(_parameter_table(schema.get("params") or [], "option"))

    examples = schema.get("examples") or []
    if examples:
        items = "".join(
            f"<dt>{_code(example['command'])}</dt><dd>{escape(str(example.get('description') or ''))}</dd>"
            for example in examples
        )
        parts.append(f"<h3>Examples</h3><dl>{items}</dl>")

    children = schema.get("subcommands") or {}
    if children:
        links = "".join(_subcommand_link(name, child) for name, child in children.items())
        parts.append(f"<h3>Subcommands</h3><ul>{links}</ul>")
    parts.append("</section>")
    parts.extend(_command_section(child, level + 1) for child in children.values())
    return "".join(parts)


def render(command: click.Command, ctx: click.Context) -> str:
    """Return the complete command tree as a standalone HTML document."""
    schema = command_schema(command, ctx, recursive=True, display=True)
    title = f"{schema.get('path') or schema.get('name') or 'Command'} help"
    return (
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(str(title))}</title><style>{_STYLES}</style></head>"
        f"<body>{_command_section(schema)}</body></html>\n"
    )
