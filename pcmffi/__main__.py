from __future__ import annotations

from typing import List

import argparse
import sys

from . import ProcMaps


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser(
        description="A CLI utility to inspect process memory maps."
    )
    parser.add_argument(
        "--pid",
        type=int,
        default=-1,
        help="PID of the process to inspect (defaults to current process).",
    )

    args = parser.parse_args(argv[1:])

    if args.pid:
        with ProcMaps(args.pid) as maps:
            for map_ in maps.maps:
                print(map_)


if __name__ == "__main__":
    main(sys.argv)
