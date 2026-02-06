import datetime
from app.services.tasks.client import tasks_client

class TasksService:
    def __init__(self):
        self.client = tasks_client

    def get_task_lists(self):
        """Returns a list of all task lists."""
        service = self.client.get_service()
        
        results = service.tasklists().list(maxResults=30).execute()
        items = results.get('items', [])
        return [{'id': item['id'], 'title': item['title']} for item in items]

    def get_tasks(self, tasklist_id: str = '@default', show_completed: bool = False):
        """Returns pending tasks from a specific list."""
        service = self.client.get_service()
        
        results = service.tasks().list(
            tasklist=tasklist_id,
            maxResults=50,
            showCompleted=show_completed,
            showHidden=show_completed
        ).execute()
        
        return results.get('items', [])

    def complete_task(self, task_id: str, tasklist_id: str = '@default'):
        """Marks a task as completed."""
        service = self.client.get_service()
        
        task = {
            'id': task_id,
            'status': 'completed'
        }
        
        service.tasks().update(
            tasklist=tasklist_id,
            task=task_id,
            body=task
        ).execute()

    def create_task(self, title: str, notes: str = "", due: str = None, tasklist_id: str = '@default'):
        """Creates a task in the specified list."""
        service = self.client.get_service()

        task = {
            'title': title,
            'notes': notes
        }
        
        if due:
            try:
                if 'T' in due:
                     dt = datetime.datetime.fromisoformat(due)
                     task['due'] = dt.isoformat() + 'Z'
            except:
                pass

        result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
        return result.get('webViewLink') or result.get('selfLink') or result.get('id')

# Singleton
tasks_service = TasksService()
