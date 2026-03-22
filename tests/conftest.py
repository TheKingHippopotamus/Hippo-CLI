"""Configure test environment for hippocli tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src directory is on sys.path so hippocli can be imported without installation
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
