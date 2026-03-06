import requests
import json

# Test health endpoint
print("Testing health endpoint...")
try:
    resp = requests.get("http://localhost:8002/health", timeout=5)
    print(f"Health: {resp.status_code} - {resp.json()}")
except Exception as e:
    print(f"Health check failed: {e}")

# Test chat endpoint
print("\nTesting chat endpoint...")
try:
    resp = requests.post(
        "http://localhost:8002/api/v1/agent/chat",
        json={
            "user_message": "Hello, what is 2+2?",
            "session_id": "test-session",
            "images": None,
            "additional_context": None,
            "llm_config": None  # Will use default
        },
        timeout=30
    )
    print(f"Chat: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response: {data.get('response', 'No response')}")
        print("SUCCESS: LLM Host is working!")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Chat test failed: {e}")
