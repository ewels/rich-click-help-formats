from __future__ import annotations

import json
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

import click
import yaml
from click.testing import CliRunner
from rich_click import RichCommand, argument, group, option

from rich_click_help_formats.carapace import SCHEMA_DIRECTIVE
from rich_click_help_formats.carapace import render as render_carapace
from rich_click_help_formats.html import render as render_html
from rich_click_help_formats.yaml import render as render_yaml


def test_distribution_registers_all_formats() -> None:
    registered = {entry_point.name for entry_point in entry_points(group="rich_click.help_formats")}
    assert {"carapace", "html", "yaml"} <= registered


def test_installed_plugins_work_without_cli_changes(cli: RichCommand, runner: CliRunner) -> None:
    carapace = runner.invoke(cli, ["--help", "carapace"])
    assert carapace.exit_code == 0
    assert yaml.safe_load(carapace.output)["name"] == "example"

    html = runner.invoke(cli, ["--help", "html"])
    assert html.exit_code == 0
    assert html.output.startswith("<!doctype html>")

    yaml_result = runner.invoke(cli, ["--help", "yaml"])
    assert yaml_result.exit_code == 0
    assert yaml.safe_load(yaml_result.output)["subcommands"]["create"]["name"] == "create"

    schema = json.loads(runner.invoke(cli, ["--help", "json"]).output)
    help_param = next(param for param in schema["params"] if param["name"] == "help")
    assert help_param["choices"] == ["markdown", "json", "compact", "carapace", "html", "yaml"]


def test_yaml_renders_full_tree(cli: RichCommand, context: Any) -> None:
    schema = yaml.safe_load(render_yaml(cli, context))
    assert schema["name"] == "example"
    assert schema["subcommands"]["create"]["path"] == "example create"


def test_yaml_converts_non_serializable_defaults(runner: CliRunner) -> None:
    @group()
    @option("--output", type=click.Path(path_type=Path), default=Path("output.txt"))
    def cli(output: Path) -> None:
        """Write a file."""

    schema = yaml.safe_load(runner.invoke(cli, ["--help", "yaml"]).output)
    output = next(param for param in schema["params"] if param["name"] == "output")
    assert output["default"] == "output.txt"


def test_carapace_renders_full_tree(cli: RichCommand, context: Any) -> None:
    output = render_carapace(cli, context)
    assert output.startswith(SCHEMA_DIRECTIVE)
    schema = yaml.safe_load(output)
    assert schema["description"] == "Manage <widgets> & related records."
    assert schema["flags"]["--help?"] == "Show this message and exit."
    assert schema["completion"]["flag"]["help"] == ["markdown", "json", "compact", "carapace", "html", "yaml"]
    assert schema["commands"][0]["name"] == "create"
    assert schema["commands"][0]["completion"]["flag"]["color"] == ["red", "blue"]


def test_carapace_maps_flags_arguments_and_hidden_commands(runner: CliRunner) -> None:
    @group()
    @option("--debug/--no-debug", help="Toggle debug.")
    @option("--tag", multiple=True, help="Tags.")
    @option("-v", "--verbose", count=True, help="Verbosity.")
    def cli(debug: bool, tag: tuple[str, ...], verbose: int) -> None:
        """Root."""

    @cli.command(aliases=["rm"], hidden=True)
    @option("--coords", type=int, nargs=2, help="Two integers.")
    @option("--format", "fmt", type=click.Choice(["json", "yaml"]), help="Output format.")
    @argument("kind", type=click.Choice(["a", "b"]))
    def remove(coords: tuple[int, ...], fmt: str, kind: str) -> None:
        """Remove one record."""

    document = yaml.safe_load(runner.invoke(cli, ["--help", "carapace"]).output)
    assert document["flags"]["--debug"] == "Toggle debug."
    assert document["flags"]["--no-debug"] == "Toggle debug."
    assert document["flags"]["--tag=*"] == "Tags."
    assert document["flags"]["-v, --verbose"] == "Verbosity."

    child = document["commands"][0]
    assert child["hidden"] is True
    assert child["aliases"] == ["rm"]
    assert child["flags"]["--coords="] == {"description": "Two integers.", "nargs": 2}
    assert child["completion"]["flag"]["format"] == ["json", "yaml"]
    assert child["completion"]["positional"] == [["a", "b"]]
    assert "Remove one record." not in runner.invoke(cli, ["--help", "html"]).output


def test_html_renders_full_tree_and_escapes_text(cli: RichCommand, context: Any) -> None:
    output = render_html(cli, context)
    assert '<html lang="en">' in output
    assert "Manage &lt;widgets&gt; &amp; related records." in output
    assert '<section class="command" id="command-ZXhhbXBsZSBjcmVhdGU">' in output
    assert '<a href="#command-ZXhhbXBsZSBjcmVhdGU"><code>create</code></a>' in output
    assert "Widget color." in output


def test_renderers_honor_short_help_and_hide_html_options(runner: CliRunner) -> None:
    @group()
    @option("--secret", hidden=True, help="Internal option.")
    def cli(secret: bool) -> None:
        """Root."""

    @cli.command(short_help="Brief summary.")
    def child() -> None:
        """A much longer description that is not the summary."""

    html = runner.invoke(cli, ["--help", "html"]).output
    assert "Internal option." not in html
    assert "<code>child</code></a>: Brief summary.</li>" in html

    document = yaml.safe_load(runner.invoke(cli, ["--help", "carapace"]).output)
    assert document["commands"][0]["description"] == "Brief summary."


def test_carapace_marks_optional_values_generically(runner: CliRunner) -> None:
    @group(context_settings={"help_option_names": ["-h"]})
    @option("--mode", is_flag=False, flag_value="auto", help="Optional mode.")
    def cli(mode: str) -> None:
        """Root."""

    document = yaml.safe_load(runner.invoke(cli, ["-h", "carapace"]).output)
    assert document["flags"]["--mode?"] == "Optional mode."
    assert document["flags"]["-h?"] == "Show this message and exit."


def test_html_command_ids_do_not_collide(runner: CliRunner) -> None:
    @group()
    def cli() -> None:
        """Root."""

    @cli.command("foo.bar")
    def dotted() -> None:
        """Dotted."""

    @cli.command("foo-bar")
    def dashed() -> None:
        """Dashed."""

    html = runner.invoke(cli, ["--help", "html"]).output
    assert html.count('id="command-') == 3
    assert 'id="command-Y2xpIGZvby5iYXI"' in html
    assert 'id="command-Y2xpIGZvby1iYXI"' in html
