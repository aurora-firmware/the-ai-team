"""Shared Rich console and JSON output helpers for the ai-team CLI."""

import json
import sys

from rich.console import Console
from rich.measure import Measurement
from rich.table import Table

UNLIMITED_WIDTH = 100_000

# Single console instance used across the entire CLI.
console = Console()


def print_json(obj: object) -> None:
    """Serialise *obj* to JSON and write it to stdout followed by a newline."""
    sys.stdout.write(json.dumps(obj, default=str) + "\n")


def print_table(table: Table) -> None:
    """Print *table*, sized to its content when the output is not a terminal."""
    if console.is_terminal:
        console.print(table)
        return
    # Piped output has no terminal width to fit; an 80-column default would cut
    # values short, so the table gets the width its content needs.
    natural_width = Measurement.get(
        console, console.options.update(max_width=UNLIMITED_WIDTH), table
    ).maximum
    Console(file=console.file, width=natural_width).print(table)
