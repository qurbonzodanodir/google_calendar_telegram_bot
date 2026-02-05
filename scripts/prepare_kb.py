import os
import sys

# Script is in /scripts, so we look one level up for project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "full_codebase.txt")

IGNORE_DIRS = {
    'venv', '__pycache__', '.git', '.idea', 'alembic', 
    '.agent', 'node_modules', '.gemini', 'scripts'
}
IGNORE_FILES = {
    '.DS_Store', 'full_codebase.txt', 'poetry.lock', 'package-lock.json', 
    'generate_code_dump.py', 'code_dump.txt'
}
VALID_EXTENSIONS = {
    '.py', '.yaml', '.yml', '.Dockerfile', '.md', '.txt', '.sh', '.json', '.env.example'
}

def is_text_file(filepath):
    """Simple check if file is likely text."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except:
        return False

def generate_dump():
    print(f"🚀 Starting Knowledge Dump...")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    
    file_count = 0
    total_size = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        # Header
        out.write(f"PROJECT CODEBASE DUMP\n")
        out.write(f"Root: {PROJECT_ROOT}\n")
        out.write(f"{'='*50}\n\n")

        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Filtering directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES:
                    continue
                    
                ext = os.path.splitext(file)[1]
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, PROJECT_ROOT)

                # Extension filter or specific inclusions like Dockerfile
                if ext not in VALID_EXTENSIONS and file != 'Dockerfile':
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        out.write(f"\n{'='*50}\n")
                        out.write(f"FILE: {relpath}\n")
                        out.write(f"{'='*50}\n")
                        out.write(content)
                        out.write("\n\n")
                        
                        file_count += 1
                        total_size += len(content)
                        # print(f"  ✅ Added: {relpath}")
                except Exception as e:
                    print(f"  ⚠️  Skipped {relpath}: {e}")

    print(f"\n🎉 Dump Complete!")
    print(f"📄 Files: {file_count}")
    print(f"💾 Size: {total_size / 1024:.2f} KB")
    print(f"📍 Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dump()
