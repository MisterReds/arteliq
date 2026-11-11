"""PyInstaller entry point: the same command as the `arteliq` console script."""
import sys

from artel.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
