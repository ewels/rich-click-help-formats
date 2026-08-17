from __future__ import annotations

from collections.abc import Iterator

import click
import pytest
from click.testing import CliRunner
from rich_click import RichCommand, argument, group, option


@pytest.fixture
def cli() -> RichCommand:
    @group()
    @option("--verbose", is_flag=True, help="Show more detail.")
    def example(verbose: bool) -> None:
        """Manage <widgets> & related records."""

    @example.command()
    @argument("name")
    @option("--color", type=click.Choice(["red", "blue"]), help="Widget color.")
    def create(name: str, color: str) -> None:
        """Create one widget."""

    return example


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def context(cli: RichCommand) -> Iterator[click.Context]:
    with cli.make_context("example", [], resilient_parsing=True) as ctx:
        yield ctx
