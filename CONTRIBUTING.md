# Contributing

Contributions, feature suggestions, and bug reports are welcome.
Open an [issue](https://github.com/ewels/rich-click-help-formats/issues) or submit a pull request.

## Local setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). Then run:

```shell
uv python pin 3.13
uv venv .venv
source .venv/bin/activate
uv sync --all-groups
prek install
```

The development environment uses the `help-json-v2` branch of rich-click.
The published package requires rich-click 1.10 or later.

## Quality checks

[prek](https://github.com/j178/prek) manages the Git hooks. The hooks check GitHub Actions files, Python formatting, Python lint rules, types, and spelling.

Run all hooks against the repository:

```shell
prek run -a
```

Run the tests:

```shell
pytest
```

Build and check the package:

```shell
python -m build
twine check dist/*
```

GitHub Actions runs these checks for each push and pull request.
