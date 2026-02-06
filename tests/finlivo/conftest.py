import sys
import os
import pytest
from agents.finlivo import config

@pytest.fixture(scope="session", autouse=True)
def add_external_project_to_path():
    """
    Adds the external FinLivo project directory to sys.path
    so we can import its modules for testing.
    """
    external_path = config.PROJECT_DIR
    if external_path not in sys.path:
        print(f"   🔗 Linking external project: {external_path}")
        sys.path.insert(0, external_path)
