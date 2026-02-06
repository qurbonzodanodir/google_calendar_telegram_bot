import os

# Define relative to this file
AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(AGENTS_DIR)

# Project Specifics
PROJECT_DIR = "/Users/nodir/Desktop/Livo/fin-app-back"
LIST_NAME = "FinLivo"
MAX_RETRIES = 3
RUN_TESTS = True # Enabled: Agent will try to find venv in project_dir

# Knowledge Base
LOCAL_KB_FILE = os.path.join(AGENTS_DIR, "knowledge_dumps", "finlivo_backend_dump_part_1.txt")
PREPARE_KB_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "prepare_kb.py")

# Test Directory
TEST_DIR = os.path.join(PROJECT_ROOT, "tests", "finlivo")
