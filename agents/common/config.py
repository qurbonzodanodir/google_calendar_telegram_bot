import os

# Base paths
AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(AGENTS_DIR)

# Knowledge Base Mappings
# 1. Project Source Directories
PROJECT_PATHS = {
    "telegram-bot": PROJECT_ROOT,  # Current Dir
    "finlivo": "/Users/nodir/Desktop/Livo/fin-app-back" # External Dir
}

# 2. Notebook IDs (Target)
NOTEBOOK_MAPPING = {
    "telegram-bot": "aa483185-30ad-4a9b-bf58-f2736cb789e5",
    "finlivo": "a5a9258f-0e2a-4c1c-9b3b-e39fcd80bb5d"
}

# 3. Output Filenames (Prevention of Collisions)
DUMP_FILENAMES = {
    "telegram-bot": "telegram_bot_dump",
    "finlivo": "finlivo_backend_dump"
}
