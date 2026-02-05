from google_auth_oauthlib.flow import InstalledAppFlow
import os

# New Scopes (Including Tasks)
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks'
]

def refresh_auth():
    print("🔄 Removing old token.json...")
    if os.path.exists('token.json'):
        os.remove('token.json')
    
    print("🚀 Starting Authentication Flow...")
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
        
    print("✅ Authentication Successful!")
    print("📄 new 'token.json' created.")
    print("👉 IMPORTANT: Update your Cloud Run 'GOOGLE_TOKEN_JSON' variable with the content of this new file!")

if __name__ == '__main__':
    refresh_auth()
