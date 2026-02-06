import os
import sys
import argparse

# Default to current project if not specified
DEFAULT_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_BASE_NAME = "full_codebase"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

IGNORE_DIRS = {
    'venv', '.venv', '__pycache__', '.git', '.idea', 'alembic', 
    '.agent', 'node_modules', '.gemini', 'scripts'
}
IGNORE_FILES = {
    '.DS_Store', 'poetry.lock', 'package-lock.json', 'uv.lock'
}
VALID_EXTENSIONS = {
    '.py', '.yaml', '.yml', '.Dockerfile', '.md', '.txt', '.sh', '.json', '.env.example', '.toml', '.ini'
}

def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except:
        return False

def generate_dump(project_root, output_dir):
    print(f"🚀 Starting Knowledge Dump...")
    print(f"📂 Project Root: {project_root}")
    print(f"📂 Output Dir: {output_dir}")
    
    file_count = 0
    part_num = 1
    current_size = 0
    
    # Open first file
    current_output_file = os.path.join(output_dir, f"{OUTPUT_BASE_NAME}_part_{part_num}.txt")
    out = open(current_output_file, 'w', encoding='utf-8')
    
    def write_header(f):
        f.write(f"PROJECT CODEBASE DUMP (Part {part_num})\n")
        f.write(f"Root: {project_root}\n")
        f.write(f"{'='*50}\n\n")

    write_header(out)

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES or file.startswith(OUTPUT_BASE_NAME):
                continue
                
            ext = os.path.splitext(file)[1]
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, project_root)

            if ext not in VALID_EXTENSIONS and file != 'Dockerfile':
                continue

            try:
                # Read content first to check size
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if we need to rotate
                content_len = len(content)
                if current_size + content_len > MAX_FILE_SIZE:
                    out.close()
                    print(f"📦 Part {part_num} closed ({current_size/1024:.2f} KB).")
                    
                    part_num += 1
                    current_size = 0
                    current_output_file = os.path.join(output_dir, f"{OUTPUT_BASE_NAME}_part_{part_num}.txt")
                    out = open(current_output_file, 'w', encoding='utf-8')
                    write_header(out)
                
                # Write
                out.write(f"\n{'='*50}\n")
                out.write(f"FILE: {relpath}\n")
                out.write(f"{'='*50}\n")
                out.write(content)
                out.write("\n\n")
                
                current_size += content_len + 100 # Approx overhead
                file_count += 1
                
            except Exception as e:
                print(f"  ⚠️  Skipped {relpath}: {e}")
    
    out.close()
    print(f"\n🎉 Dump Complete!")
    print(f"📄 Total Processed Files: {file_count}")
    print(f"📚 Total Parts: {part_num}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Codebase Dump")
    parser.add_argument("--root", help="Project Root Directory", default=DEFAULT_PROJECT_ROOT)
    parser.add_argument("--out", help="Output Directory", default=DEFAULT_PROJECT_ROOT)
    args = parser.parse_args()
    
    generate_dump(args.root, args.out)
