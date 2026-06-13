"""
Root conftest for shared-py tests.

Ensures the shared_py package is importable even without pip install -e.
"""

import sys
from pathlib import Path

# Add the shared-py package root to sys.path so 'shared_py' is importable
pkg_root = Path(__file__).parent
if str(pkg_root) not in sys.path:
    sys.path.insert(0, str(pkg_root))
