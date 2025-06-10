import sys, os
import pytest
import importlib.util
from unittest.mock import patch

# 🔧 Fix: Add backend/ to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

# Now election_routes.py can import `from services...` correctly
ROUTES_PATH = os.path.join(BACKEND_PATH, "routes/admin/election_routes.py")
if not os.path.exists(ROUTES_PATH):
    raise FileNotFoundError(f"❌ Cannot locate election_routes.py at: {ROUTES_PATH}")

role_patch = None

def pytest_configure(config):
    global role_patch
    spec = importlib.util.spec_from_file_location("election_routes", ROUTES_PATH)
    election_routes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(election_routes)

    role_patch = patch.object(election_routes, "role_required", lambda _: (lambda f: f))
    role_patch.start()

def pytest_sessionfinish(session, exitstatus):
    if role_patch:
        role_patch.stop()

@pytest.fixture(autouse=True)
def mock_role_required():
    with patch("utilities.auth_utils.role_required", lambda role: lambda fn: fn):
        yield