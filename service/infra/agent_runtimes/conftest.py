from pathlib import Path

import pytest


# Wraps pytest's standard tmp_path (which creates the directory)
# as a str to match RunExecutor's signature. The directory must exist
# before RunExecutor runs, or TemporaryDirectory(dir=...) raises.
@pytest.fixture
def workspace_base_path(tmp_path: Path) -> str:
    return str(tmp_path)
