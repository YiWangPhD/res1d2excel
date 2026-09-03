"""Command-line entry point for res1d2excel."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from . import res1d2excel


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="res1d2excel",
        description=(
            "Extract MIKE 1D and EPANET result files to Excel and HTML outputs. "
            "Run without an input file to create template files in the current folder."
        ),
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to a res1d2excel .xlsx or .json input configuration file.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()
    argv = [str(Path(args.input_file))] if args.input_file else []
    res1d2excel.main(argv)
