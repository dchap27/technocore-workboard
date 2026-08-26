"""Command-line entry point.

The first release intentionally exposes only protocol inspection. Network and
identity commands are added after signature test vectors are in place.
"""

from __future__ import annotations

import argparse

from technocore_workboard import __version__


def main() -> None:
    parser = argparse.ArgumentParser(prog="workboard")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()
    parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
