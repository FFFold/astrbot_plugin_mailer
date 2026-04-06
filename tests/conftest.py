from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PARENT_ROOT = PLUGIN_ROOT.parent
WORKSPACE_ROOT = PLUGIN_ROOT.parents[4]

for path in (WORKSPACE_ROOT, PARENT_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
