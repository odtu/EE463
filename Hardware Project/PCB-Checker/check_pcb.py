#!/usr/bin/env python3
"""EE463 PCB checker.

Usage:
    python check_pcb.py MyBoard.kicad_pcb
    python check_pcb.py path/to/project_folder
    python check_pcb.py submission.zip --open
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pcbcheck.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
