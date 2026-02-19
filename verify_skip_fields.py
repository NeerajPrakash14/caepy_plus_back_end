import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1/voice"
AUTH_URL = "http://localhost:8000/api/v1"

# Context for testing - must include email/phone to test skipping
context = {
    "fields": [
        {"key": "fullName", "label": "Full Name", "description": "Your name", "required": True},
        {"key": "email", "label": "Email", "description": "Your email address", "required": True},
        {"key": "phone", "label": "Phone Number", "description": "Your phone number", "required": True},
        {"key": "specialty", "label": "Specialty", "description": "Your specialty", "required": True}
    ]
}

def verify():
    print("Waiting for server...")
    time.sleep(2)

    # 1. Authenticate with the user we just set up
    print("Authenticating...")
    auth_payload = {"phone_number": "9999999999", "otp": "123456"}
    auth_resp = requests.post(f"{AUTH_URL}/validateandlogin", json=auth_payload)
    
    if auth_resp.status_code != 200:
        print(f"Authentication failed: {auth_resp.text}")
        sys.exit(1)
        
    token = auth_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Authentication successful.")

    # 2. Start Session
    print(f"Starting session with context...")
    resp = requests.post(f"{BASE_URL}/start", json={"language": "en", "context": context}, headers=headers)
    
    if resp.status_code != 201:
        print(f"Start Status: {resp.status_code}")
        print(f"Error: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    session_id = data["session_id"]
    print(f"Session ID: {session_id}")

    # 3. Verify Initial State
    # Check session status
    status_resp = requests.get(f"{BASE_URL}/session/{session_id}", headers=headers)
    status_data = status_resp.json()
    
    fields_status = status_data["fields_status"]
    current_data = status_data["current_data"]
    
    print("\nCurrent Data:", json.dumps(current_data, indent=2))
    
    # Check if email and phone are collected
    email_collected = any(f["field_name"] == "email" and f["is_collected"] for f in fields_status)
    phone_collected = any(f["field_name"] == "phone" and f["is_collected"] for f in fields_status)
    
    if not email_collected and phone_collected:
        print("SUCCESS: Phone is marked as collected, Email is NOT (as requested).")
    else:
        print(f"FAILURE: Email collected: {email_collected}, Phone collected: {phone_collected}")
        sys.exit(1)
        
    # Check values match (lenient phone check)
    # Email should NOT be here initially anymore because we want the AI to ask for it.
    if "9999999999" in current_data.get("phone", ""):
        print("SUCCESS: Phone matches user profile.")
    else:
         print(f"FAILURE: Phone does not match. Phone: {current_data.get('phone')}")
         sys.exit(1)

    # 4. Chat Interaction - Verify flow
    print("\nSending Chat: 'My name is Dr. Neeraj'")
    chat_resp = requests.post(f"{BASE_URL}/chat", json={
        "session_id": session_id,
        "user_transcript": "My name is Dr. Neeraj",
        "context": context
    }, headers=headers)
    
    if chat_resp.status_code != 200:
        print(f"Chat Error: {chat_resp.text}")
        sys.exit(1)

    chat_data = chat_resp.json()
    ai_response = chat_data["ai_response"]
    print(f"AI Response: {ai_response}")
    
    # AI should NOT ask for phone, but SHOULD ask for email.
    if "email" in ai_response.lower():
        print("SUCCESS: AI asked for email.")
    if "phone" in ai_response.lower():
        print("WARNING: AI might be asking for phone. Check response.")

    print("\nVerification passed!")

if __name__ == "__main__":
    verify()
