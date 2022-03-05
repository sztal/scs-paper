"""Factory for command-line parsers for downloading networks.

The parser handles only one argument (``force``)
and provides some basic description and help.
"""
from pathlib import Path
from argparse import ArgumentParser


def get_parser(filename: str, desc: str) -> ArgumentParser:
    """Get command-line argument parser."""
    here = Path(filename).parent
    name = "-".join(here.stem.split("-")[1:])

    parser = ArgumentParser(
        description=desc.format(analysis=name)
    )
    parser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        default=False,
        help="Force re-downloading even if dataset exist."
    )
    return parser

