from __future__ import annotations

import sys

from deezer_search.cli import SongSearchCLI


def main() -> int:
    cli = SongSearchCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
