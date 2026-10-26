import os
import sys
import pytest

# Ensure backend root directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

@pytest.fixture(autouse=True)
def clean_environment():
    """Ensures consistent test environment variables."""
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("LANGFUSE_ENABLED", "false")
    yield
