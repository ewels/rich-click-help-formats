# rich-click-help-formats

[![PyPI](https://img.shields.io/pypi/v/rich-click-help-formats?logo=pypi)](https://pypi.org/project/rich-click-help-formats/)
[![Test and build](https://github.com/ewels/rich-click-help-formats/actions/workflows/pytest.yml/badge.svg)](https://github.com/ewels/rich-click-help-formats/actions/workflows/pytest.yml)
[![Lint code](https://github.com/ewels/rich-click-help-formats/actions/workflows/prek.yml/badge.svg)](https://github.com/ewels/rich-click-help-formats/actions/workflows/prek.yml)

`rich-click-help-formats` adds optional output formats to every CLI that uses
[rich-click](https://github.com/ewels/rich-click). The
[rich-click structured-help documentation](https://ewels.github.io/rich-click/documentation/machine_readable_help/)
describes the native formats.

With this package installed, the available formats are:

- **Native:** `--help markdown` emits the complete command tree as Markdown.
- **Native:** `--help json` emits the complete command tree as JSON.
- **Native:** `--help compact` emits concise text for coding agents.
- **Plugin:** `--help yaml` emits the complete command tree as YAML.
- **Plugin:** `--help html` emits a complete, standalone HTML help page.
- **Plugin:** `--help carapace` emits a complete [Carapace](https://carapace.sh) command specification as YAML.

Install this package in the same Python environment as the CLI:

```console
pip install rich-click-help-formats
```

This package requires rich-click 1.10 or later. The CLI does not need a code change. rich-click discovers the formats through Python package entry points.

## Add another format

Keep each renderer in a separate module. A renderer accepts the Click command and context. It returns the complete output as a string:

```python
# src/my_help_formats/outline.py

from rich_click.help_json import command_schema


def command_paths(schema):
    paths = [schema["path"]]
    for child in schema.get("subcommands", {}).values():
        paths.extend(command_paths(child))
    return paths


def render(command, ctx):
    schema = command_schema(command, ctx, recursive=True)
    return "\n".join(command_paths(schema)) + "\n"
```

Register the callable in your package's `pyproject.toml`:

```toml
[project.entry-points."rich_click.help_formats"]
outline = "my_help_formats.outline:render"
```

After installation, every rich-click CLI in that Python environment accepts `--help outline`.

Use a short, lowercase entry-point name. Use one entry point for each format. This structure keeps formats independent and makes new formats easy to add.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the local setup and quality checks.
