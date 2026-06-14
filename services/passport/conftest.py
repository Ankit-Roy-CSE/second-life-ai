"""
Product Passport Service test configuration.

Adds shared-py and the service app to sys.path for local test runs
without requiring full editable installs.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "packages" / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent))
