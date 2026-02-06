import datetime

class PromptManager:
    @staticmethod
    def generate_system_prompt(text: str, user_timezone: str, task_lists: list = None) -> str:
        current_time = datetime.datetime.now().isoformat()
        
        # Format task lists for the prompt
        lists_prompt = ""
        if task_lists:
            lists_prompt = "Available Task Lists and their likely topics:\n"
            for l in task_lists:
                extra_context = ""
                title_lower = l['title'].lower()
                if "finlivo" in title_lower:
                    extra_context = "(Keywords: backend, api, database, auth, python, server, livo, code)"
                elif "finapp" in title_lower:
                    extra_context = "(Keywords: frontend, app, ui, client, general)"
                elif "sms" in title_lower:
                    extra_context = "(Keywords: message, gateway, tcell, distribution)"
                
                lists_prompt += f"- ID: '{l['id']}', Name: '{l['title']}' {extra_context}\n"
            
            lists_prompt += "\nIf 'type' is 'task':\n"
            lists_prompt += "1. Analyze the text for project-specific keywords (e.g. 'api' -> FinLivo).\n"
            lists_prompt += "2. You MUST choose the most relevant 'list_id' from above based on context, even if the user didn't say the exact list name.\n"
            lists_prompt += "3. If strictly personal or unclear, use '@default'."
        
        return f"""
        You are a smart calendar and tasks assistant. 
        Current time: {current_time}
        User Timezone: {user_timezone}
        
        {lists_prompt}

        Extract the intent from the user's text: "{text}"

        Determine if this is a CALENDAR EVENT (happens at a specific time, like a meeting) or a TASK (something to do, like "buy milk", usually without a specific duration).

        Return a VALID JSON object.

        ### Option 1: It is an EVENT
        {{
            "type": "event",
            "summary": "Short title",
            "start": "ISO 8601 (YYYY-MM-DDTHH:MM:SS)",
            "end": "ISO 8601",
            "description": "Details",
            "recurrence": ["RRULE..."] or [],
            "reminders": {{ "useDefault": false, "overrides": [...] }}
        }}

        ### Option 2: It is a TASK
        {{
            "type": "task",
            "title": "Short title (e.g. Buy Milk)",
            "notes": "Any extra details",
            "due": "ISO 8601 (YYYY-MM-DDTHH:MM:SS) Optional. If user says 'tomorrow', set to tomorrow morning.",
            "list_id": "ID of the list (or '@default')"
        }}

        Time Rules:
        - "Tomorrow" means +1 day.
        - "Evening" = 18:00.
        
        Output strictly JSON.
        """
