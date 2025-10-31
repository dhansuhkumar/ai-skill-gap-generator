from backend.app import create_app

def test_recommend_endpoint():
    app = create_app()
    client = app.test_client()

    payload = {
        "role": "Web Developer",
        "skills": ["js", "html"]
    }

    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "missing_skills" in data
    assert "recommended_projects" in data
 
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["recommended_projects"], list)
