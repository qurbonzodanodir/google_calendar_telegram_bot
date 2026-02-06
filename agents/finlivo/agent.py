import time
import os
import sys
from app.services.tasks.service import tasks_service
from agents.common import knowledge, llm, tools
from agents.finlivo import config

class FinLivoAgent:
    def __init__(self):
        self.context = ""
        self.list_id = None

    def start(self):
        print(f"👨‍💻 FinLivo Agent (Senior Level) started!")
        print(f"📂 Watching List: {config.LIST_NAME}")
        print(f"📂 Project Dir: {config.PROJECT_DIR}")
        
        # Load Brain
        self.context = knowledge.load_local_context(config.LOCAL_KB_FILE)
        
        # Find List ID
        try:
            lists = tasks_service.get_task_lists()
            self.list_id = next((l['id'] for l in lists if l['title'] == config.LIST_NAME), None)
            if not self.list_id:
                print(f"❌ List '{config.LIST_NAME}' not found.")
                return
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return

        self.loop()

    def loop(self):
        while True:
            try:
                tasks = tasks_service.get_tasks(tasklist_id=self.list_id)
                if tasks:
                    for task in tasks:
                        self.process_task(task)
                    time.sleep(10)
                else:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\n🛑 Agent stopped.")
                knowledge.update_knowledge_base(
                    script_path=config.PREPARE_KB_SCRIPT,
                    project_root=config.PROJECT_DIR,
                    output_dir=os.path.dirname(config.LOCAL_KB_FILE)
                )
                break
            except Exception as e:
                print(f"Loop Error: {e}")
                time.sleep(10)

    def process_task(self, task):
        title = task['title']
        if title.startswith("[FAILED]"):
            print(f"   ⏭️ Skipping failed task: {title}")
            return

        notes = task.get('notes', '')
        print(f"\n⚡️ TASK: {title}")
        
        # Find File
        target_file = self.find_file(title, notes)
        
        if target_file and os.path.exists(target_file):
            print(f"   🔨 Editing {target_file}...")
            result = llm.apply_senior_edit(
                file_path=target_file, 
                instruction=title, 
                project_context=self.context,
                project_root=config.PROJECT_DIR,
                max_retries=config.MAX_RETRIES,
                run_tests=config.RUN_TESTS
            )
            print(f"   {result}")
            
            if "✅" in result:
                tasks_service.complete_task(task['id'], tasklist_id=self.list_id)
            else:
                # Failure Case: Rename task so we don't pick it up again
                new_title = f"[FAILED] {title}"
                tasks_service.update_task_title(task['id'], new_title, tasklist_id=self.list_id)
                print(f"   ⚠️ Marked task as FAILED in Google Tasks.")
        else:
            print(f"   🤔 No valid file found for task. mention filename in title/notes.")
            # Verify if we should skip silent items to avoid loop log spam
            # For now, just pass

    def find_file(self, title, notes):
        # 1. Smart Discovery via LLM
        print("   🔍 Scanning project structure...")
        structure = tools.get_project_structure(config.PROJECT_DIR)
        
        task_desc = f"{title}. {notes}"
        recommended_file = llm.find_relevant_file(task_desc, structure)
        
        if recommended_file:
            full_path = os.path.join(config.PROJECT_DIR, recommended_file)
            if os.path.exists(full_path):
                print(f"   🤖 AI identified target: {recommended_file}")
                return full_path
            else:
                 print(f"   ⚠️ AI suggested non-existent file: {recommended_file}")

        # 2. Fallback to simple heuristic
        potential_files = [w for w in (title + " " + notes).split() if '.' in w]
        if potential_files:
             print(f"   ⚠️ Falling back to manual filename: {potential_files[0]}")
             return os.path.join(config.PROJECT_DIR, potential_files[0])
        
        return None
