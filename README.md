# rich-click-help-formats

[![PyPI](https://img.shields.io/pypi/v/rich-click-help-formats?logo=pypi)](https://pypi.org/project/rich-click-help-formats/)
[![Test and build](https://github.com/ewels/rich-click-help-formats/actions/workflows/pytest.yml/badge.svg)](https://github.com/ewels/rich-click-help-formats/actions/workflows/pytest.yml)
[![Lint code](https://github.com/ewels/rich-click-help-formats/actions/workflows/prek.yml/badge.svg)](https://github.com/ewels/rich-click-help-formats/actions/workflows/prek.yml)

`rich-click-help-formats` adds two optional output formats to every CLI that uses
[rich-click](https://github.com/ewels/rich-click):

- `--help carapace` emits a complete [Carapace](https://carapace.sh) command specification as YAML.
- `--help html` emits a complete, standalone HTML help page.

Install this package in the same Python environment as the CLI:

```console
pip install rich-click-help-formats
```

This package requires rich-click 1.10 or later. The CLI does not need a code change. rich-click discovers the formats through Python package entry points.

## Add another format

Keep each renderer in a separate module. A renderer accepts the Click command and context. It returns the complete output as a string:

```python
# src/my_help_formats/yaml.py
import yaml

from rich_click.help_json import command_schema


def render(command, ctx):
    schema = command_schema(command, ctx, recursive=True)
    return yaml.safe_dump(schema, sort_keys=False)
```

Register the callable in your package's `pyproject.toml`:

```toml
[project.entry-points."rich_click.help_formats"]
yaml = "my_help_formats.yaml:render"
```

After installation, every rich-click CLI in that Python environment accepts `--help yaml`.

Use a short, lowercase entry-point name. Use one entry point for each format. This structure keeps formats independent and makes new formats easy to add.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the local setup and quality checks.
