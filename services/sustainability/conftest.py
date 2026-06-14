"""
Test config for the Sustainability Service — adds shared-py to sys.path.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "packages" / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent))
