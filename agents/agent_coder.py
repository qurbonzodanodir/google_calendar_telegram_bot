import sys
import os
import time
import shutil

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tasks import tasks_service
from app.services.groq_service import groq_service
from app.core import config

# CONFIGURATION
# 1. Which list to watch?
TARGET_LIST_NAME = "FinLivo" 

# 2. Where is your project located? 
# (Update this to your actual project path!)
PROJECT_BASE_DIR = "/Users/nodir/Desktop/Livo/fin-app-back" 

def apply_ai_edit(file_path, instruction):
    """Reads file, asks Groq to edit it, saves result."""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    print(f"   📖 Reading {file_path}...")
    with open(file_path, 'r') as f:
        code = f.read()

    # Simple Prompt for Code Editing
    prompt = f"""
    You are a Senior Python Developer.
    
    USER INSTRUCTION: {instruction}
    
    FILE CONTENT:
    {code}
    
    Output the FULL modified file content. Do not use Markdown blocks (```). Just raw code.
    """
    
    # We use the text model directly here (hacky re-use of groq_service or direct client)
    # Let's reuse the client from groq_service
    try:
        response = groq_service.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        new_code = response.choices[0].message.content
        
        # Clean up markdown if AI added it naturally
        if new_code.startswith("```python"): new_code = new_code[9:]
        if new_code.startswith("```"): new_code = new_code[3:]
        if new_code.endswith("```"): new_code = new_code[:-3]
        
        # Backup
        backup_path = file_path + ".bak"
        shutil.copy(file_path, backup_path)
        
        # Write
        with open(file_path, 'w') as f:
            f.write(new_code)
            
        return f"✅ Edited {os.path.basename(file_path)} (Backup: .bak)"
        
    except Exception as e:
        return f"❌ AI Error: {e}"

def run_agent():
    print(f"👨‍💻 Coder Agent for '{TARGET_LIST_NAME}' started!")
    print(f"📂 Working on: {PROJECT_BASE_DIR}")
    
    # Authenticate/Find List
    lists = tasks_service.get_task_lists()
    list_id = next((l['id'] for l in lists if l['title'] == TARGET_LIST_NAME), None)
    
    if not list_id:
        print(f"❌ List '{TARGET_LIST_NAME}' not found.")
        return

    while True:
        try:
            tasks = tasks_service.get_tasks(tasklist_id=list_id)
            if tasks:
                for task in tasks:
                    title = task['title']
                    notes = task.get('notes', '')
                    print(f"\n⚡️ TASK: {title}")
                    
                    # Heuristic: Expect note to contain filename (e.g. "app/main.py")
                    # If not, we skip (or you can implementing searching)
                    target_file = None
                    instruction = title
                    
                    # Try to find a file in the project that matches words in the task
                    # Very simple logic: if a word in Notes or Title ends with .py
                    potential_files = [w for w in (title + " " + notes).split() if '.' in w]
                    
                    if potential_files:
                        # Construct full path
                        candidate = os.path.join(PROJECT_BASE_DIR, potential_files[0])
                        if os.path.exists(candidate):
                            target_file = candidate
                        else:
                            print(f"   ⚠️ File mentioned '{potential_files[0]}' not found in project.")
                    
                    if target_file:
                        print(f"   🔨 Editing {target_file}...")
                        result = apply_ai_edit(target_file, instruction)
                        print(f"   {result}")
                        tasks_service.complete_task(task['id'], tasklist_id=list_id)
                    else:
                        print("   🤔 No filename matched. Please specify file in task title/notes (e.g., 'Fix app/main.py').")
                        # We don't complete it so user can fix description
            
                time.sleep(10)
            else:
                time.sleep(10)

        except KeyboardInterrupt:
            break
        except Exception as e:
             print(f"Error: {e}")
             time.sleep(10)

if __name__ == "__main__":
    run_agent()
