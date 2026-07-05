"""PyInstaller entry shim — freezes the AXIOM CLI into a standalone binary."""
from axiom.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
