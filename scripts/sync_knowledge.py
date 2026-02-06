import os
import argparse
import sys
import json
import shutil

# Add project root to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.common.config import NOTEBOOK_MAPPING, PROJECT_PATHS, DUMP_FILENAMES, PROJECT_ROOT
from scripts.prepare_kb import generate_dump

def sync(project_name):
    # 1. Validation
    notebook_id = NOTEBOOK_MAPPING.get(project_name)
    project_source_path = PROJECT_PATHS.get(project_name)
    dump_base_name = DUMP_FILENAMES.get(project_name)

    if not all([notebook_id, project_source_path, dump_base_name]):
        print(f"❌ Error: Configuration missing for project '{project_name}'.")
        sys.exit(1)

    if not os.path.exists(project_source_path):
        print(f"❌ Error: Project source path not found: {project_source_path}")
        sys.exit(1)

    print(f"🧠 Syncing '{project_name}'...")
    print(f"   📂 Source: {project_source_path}")
    print(f"   📓 Notebook ID: {notebook_id}")
    
    # Define Output Dir (Local Cache)
    # We store all dumps in the agent's knowledge_dumps folder
    output_dir = os.path.join(PROJECT_ROOT, "knowledge_dumps")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. Generate Dump
    # prepare_kb always creates "full_codebase_part_X.txt"
    generate_dump(project_source_path, output_dir)
    
    # 3. Rename/Move to unique filename
    generated_file = os.path.join(output_dir, "full_codebase_part_1.txt")
    if not os.path.exists(generated_file):
        print(f"❌ Error: Dump generation failed (file not found).")
        sys.exit(1)
        
    final_file = os.path.join(output_dir, f"{dump_base_name}_part_1.txt")
    shutil.move(generated_file, final_file)
    print(f"   ✅ Created: {final_file}")

    # Output JSON for the Agent to parse
    result = {
        "status": "ready_to_upload",
        "project": project_name,
        "notebook_id": notebook_id,
        "file_path": final_file
    }
    print(f"\nJSON_RESULT:{json.dumps(result)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Knowledge Base for Sync")
    parser.add_argument("--project", help="Project Key (e.g. telegram-bot)", required=True)
    args = parser.parse_args()
    
    sync(args.project)
