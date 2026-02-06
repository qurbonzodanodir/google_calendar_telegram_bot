from app.services.tasks.service import tasks_service
from app.services.ai.service import ai_service
from app.core import config

# Mock settings to avoid error if loading from env fails in script
if not config.settings.GROQ_API_KEY:
    import os
    config.settings.GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def test_routing():
    print("🚀 Fetching Task Lists...")
    try:
        lists = tasks_service.get_task_lists()
        print(f"✅ Found {len(lists)} lists:")
        for l in lists:
            print(f"   - {l['title']} (ID: {l['id']})")
    except Exception as e:
        print(f"❌ Failed to fetch lists: {e}")
        return

    # Test Case: Smart Routing (No explicit project name)
    text = "Fix authentication bug in the api"
    print(f"\n🧠 Asking AI Service: '{text}'...")
    
    event_data = await ai_service.parse_event(text, task_lists=lists)
    print(f"🤖 AI Response: {event_data}")
    
    target_list_id = event_data.get('list_id')
    print(f"🎯 Target List ID: {target_list_id}")

    if target_list_id and target_list_id != '@default':
        print(f"✅ Groq successfully routed to a specific list!")
    else:
        print(f"⚠️ Groq defaulted to main list (maybe 'FinApp' list doesn't exist yet?)")

if __name__ == "__main__":
    asyncio.run(test_routing())
