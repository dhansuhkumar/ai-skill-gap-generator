import requests
import uuid
import json
import time

BASE_URL = "http://localhost:8080"

def test_flow():
    # 1. Register/Login
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    password = "password123"
    
    print(f"🔹 Registering {username}...")
    try:
        requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
    except:
        pass # Might already exist

    print(f"🔹 Logging in...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if res.status_code != 200:
        print(f"❌ Login failed: {res.text}")
        return
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # 2. Confirm Skills
    print(f"🔹 Confirming Skills...")
    skills = [{"name": "Python", "confidence": 90}, {"name": "SQL", "confidence": 80}]
    res = requests.post(f"{BASE_URL}/api/confirm_skills", json={"skills": skills}, headers=headers)
    if res.status_code != 200:
        print(f"❌ Confirm Skills failed: {res.text}")
        return
    print("✅ Skills confirmed")

    # 3. Analyze Role Gaps (Deterministic)
    print(f"🔹 Analyzing Gap for 'Backend Developer'...")
    start_time = time.time()
    res = requests.post(f"{BASE_URL}/api/analyze_role_gaps", json={
        "role": "Backend Developer",
        "skills": ["Python", "SQL"]
    }, headers=headers)
    duration = time.time() - start_time
    
    if res.status_code != 200:
        print(f"❌ Analyze Gaps failed: {res.text}")
        return
        
    data = res.json()
    missing = data.get("missing_skills", [])
    print(f"   Missing Skills: {missing}")
    
    # Check if 'Docker' or 'REST APIs' is in missing (from our role_data.json)
    if "Docker" in missing or "REST APIs" in missing:
        print("✅ Deterministic gap analysis correctly found missing skills.")
    else:
        print(f"⚠️ Gap analysis result unexpected: {missing}")
        
    if duration > 1.0:
        print(f"⚠️ Warning: Gap analysis took {duration:.2f}s (should be instant)")
    else:
        print(f"✅ Performance: Gap analysis took {duration:.2f}s (Instant)")

    # 4. Generate Learning Path (AI)
    print(f"🔹 Generating Learning Path (Simulated User Inputs)...")
    payload = {
        "target_role": "Backend Developer",
        "selected_skills": ["Docker", "REST APIs"],
        "learning_pace": "Intensive",
        "time_commitment": "2 hours",
        "duration": "2 weeks",
        "project_type": "real-world",
        "include_youtube": True,
        "additional_context": "I know basic Python."
    }
    
    res = requests.post(f"{BASE_URL}/api/generate_learning_path", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"❌ Generate Plan failed: {res.text}")
        return
        
    plan = res.json()
    lp = plan.get("learning_path", {})
    
    if "skills" in lp and "Docker" in lp["skills"]:
        print("✅ Learning path generated successfully with correct structure.")
    else:
        print(f"❌ Learning path missing expected content: {plan.keys()}")
        
    if plan.get("source") != "heuristic": # Might be heuristic if AI fails/mocks, check logic
        print(f"✅ Source: {plan.get('source')}")

if __name__ == "__main__":
    test_flow()
