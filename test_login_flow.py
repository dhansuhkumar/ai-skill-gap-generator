import requests
import json

BASE_URL = "http://localhost:8080/auth"

def test_flow():
    email = "test_debug_new@example.com"
    password = "password123"

    # 1. Register
    print(f"Registering {email}...")
    try:
        reg_resp = requests.post(f"{BASE_URL}/register", json={"email": email, "password": password})
        print(f"Register status: {reg_resp.status_code}")
        print(f"Register response: {reg_resp.text}")
    except Exception as e:
        print(f"Register failed: {e}")

    # 2. Login
    print(f"\nLogging in as {email}...")
    try:
        login_resp = requests.post(f"{BASE_URL}/login", json={"email": email, "password": password})
        print(f"Login status: {login_resp.status_code}")
        print(f"Login response: {login_resp.text}")
        
        if login_resp.status_code == 200:
            print("Login SUCCESS!")
        else:
            print("Login FAILED!")

    except Exception as e:
        print(f"Login failed: {e}")

if __name__ == "__main__":
    test_flow()
