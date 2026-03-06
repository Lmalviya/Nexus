import requests
import json
import time

BASE_URL = "http://localhost:8000"

def verify_flow():
    # 1. Register/Login
    email = f"test_{int(time.time())}@example.com"
    password = "password123"
    print(f"Registering user: {email}")
    
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "password": password,
        "organization_name": "Test Org",
        "organization_slug": f"test-org-{int(time.time())}"
    })
    
    if resp.status_code != 200:
        print(f"Registration failed: {resp.text}")
        return
        
    token = resp.json()['token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Session
    print("Creating session...")
    resp = requests.post(f"{BASE_URL}/conversations", json={"title": "Test Session"}, headers=headers)
    session_id = resp.json()['session']['session_id']
    print(f"Session ID: {session_id}")
    
    # 3. Send Message 1 (Context Setter)
    print("Sending Message 1: 'My name is NexusTest'")
    resp = requests.post(f"{BASE_URL}/conversations/{session_id}/chat", json={
        "user_message": "My name is NexusTest",
        "model": "llama3",
        "provider": "ollama"
    }, headers=headers)
    
    if resp.status_code != 200:
        print(f"Chat failed: {resp.text}")
        return
        
    print("Response 1 received.")
    
    # 4. Send Message 2 (Context Retriever)
    print("Sending Message 2: 'What is my name?'")
    resp = requests.post(f"{BASE_URL}/conversations/{session_id}/chat", json={
        "user_message": "What is my name?",
        "model": "llama3",
        "provider": "ollama"
    }, headers=headers)
    
    data = resp.json()
    assistant_response = data['orchestration_response']['response']
    print(f"Assistant Response: {assistant_response}")
    
    if "NexusTest" in assistant_response:
        print("SUCCESS: Context was preserved!")
    else:
        print("FAILURE: Context was NOT preserved.")

    # 5. Verify History Persistence
    print("Fetching Session History...")
    resp = requests.get(f"{BASE_URL}/conversations/{session_id}", headers=headers)
    history = resp.json()['session']['messages']
    print(f"History length: {len(history)}")
    
    if len(history) >= 4: # 2 user + 2 assistant
        print("SUCCESS: History persisted.")
    else:
        print("FAILURE: History missing.")

if __name__ == "__main__":
    try:
        verify_flow()
    except Exception as e:
        print(f"Error: {e}")
