import os
import subprocess
from agents.common import config

def load_local_context(kb_file_path: str) -> str:
    """Reads the full project codebase dump to provide context."""
    if os.path.exists(kb_file_path):
        try:
            with open(kb_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"🧠 Local Knowledge Base loaded ({len(content)} chars)")
            return content
        except Exception as e:
            print(f"⚠️ Failed to load Local KB: {e}")
            return ""
    else:
        print(f"⚠️ Local Knowledge Base file not found at {kb_file_path}. Running blind.")
        return ""

def update_knowledge_base(script_path: str, project_root: str, output_dir: str):
    """Runs the prepare_kb.py script to refresh the dump."""
    print(f"\n📚 Updating Knowledge Base Dump...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        subprocess.run([
            "python3", script_path, 
            "--root", project_root,
            "--out", output_dir
        ], check=True)
        print(f"✅ KB Updated in: {output_dir}")
    except Exception as e:
        print(f"❌ Failed to update KB: {e}")
