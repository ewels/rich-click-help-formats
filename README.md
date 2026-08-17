# rich-click-help-formats

[![PyPI](https://img.shields.io/pypi/v/rich-click-help-formats?logo=pypi)](https://pypi.org/project/rich-click-help-formats/)
[![Test and build](https://github.com/ewels/rich-click-help-formats/actions/workflows/pytest.yml/badge.svg)](https://github.com/ewels/rich-click-help-formats/actions/workflows/pytest.yml)
[![Lint code](https://github.com/ewels/rich-click-help-formats/actions/workflows/prek.yml/badge.svg)](https://github.com/ewels/rich-click-help-formats/actions/workflows/prek.yml)

[`rich-click`](https://github.com/ewels/rich-click) is a Python library that tool developers use to make command-line tool output look nice, particularly `--help`. As of v1.10 it is [also able to produce](https://ewels.github.io/rich-click/documentation/machine_readable_help/) help output as markdown, json and a compact form for LLMs. `rich-click-help-formats` extends this functionality to add optional output formats:

- `--help yaml` emits the complete command tree as YAML.
- `--help html` emits a complete, standalone HTML help page.
- `--help carapace` emits a complete [Carapace](https://carapace.sh) command specification as YAML.

This plugin can be used by tool developers or end users. When installed, these options will be available for any CLI you use that is built using `rich-click`.

## Installation

Install this package in the same Python environment as the CLI:

```bash
pip install rich-click-help-formats
```

This package requires rich-click 1.10 or later. The CLI itself does not need a code change. rich-click discovers the formats through Python package entry points.

## Contributions

Controbutions are welcome. If you would like to add another format, please open a pull-request!

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for the local setup and quality checks.
