import sys
import os
import time
import random

# Add parent dir to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tasks.service import tasks_service

TARGET_LIST_NAME = "FinApp" # Change this to "Sms Target" etc.

def run_agent():
    print(f"🤖 Agent '{TARGET_LIST_NAME}' started!")
    print("👀 Watching for tasks...")

    # 1. Find List ID
    lists = tasks_service.get_task_lists()
    list_id = None
    for l in lists:
        if l['title'] == TARGET_LIST_NAME:
            list_id = l['id']
            break
    
    if not list_id:
        print(f"❌ List '{TARGET_LIST_NAME}' not found. Please create it in Google Tasks first.")
        return

    print(f"✅ Found List ID: {list_id}")

    # 2. Main Loop
    while True:
        try:
            tasks = tasks_service.get_tasks(tasklist_id=list_id)
            
            if not tasks:
                print("💤 No new tasks... sleeping.")
            else:
                for task in tasks:
                    print(f"\n⚡️ ACTION REQUIRED: {task['title']}")
                    print(f"   Notes: {task.get('notes', 'No notes')}")
                    
                    # Simulation of work
                    print("   🔨 Asking generic AI to fix this...")
                    time.sleep(2) 
                    
                    print("   ✅ Done! Marking as completed.")
                    tasks_service.complete_task(task['id'], tasklist_id=list_id)
            
            time.sleep(10) # Check every 10 seconds

        except KeyboardInterrupt:
            print("\n🛑 Agent stopped.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_agent()



#vapros pochemu tam 68 mb files tak mnogo 