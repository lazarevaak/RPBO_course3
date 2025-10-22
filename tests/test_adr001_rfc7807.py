def test_rfc7807_404_and_422(client):
    # 404
    r1 = client.get("/topics/999999")
    assert r1.status_code == 404
    assert r1.headers.get("content-type", "").startswith("application/problem+json")
    b1 = r1.json()
    assert b1["title"] == "HTTP Error" and b1["status"] == 404
    assert "correlation_id" in b1 and "instance" in b1

    # 422 (валидация ProgressUpdate вне [0;100])
    r2 = client.put("/topics/1/progress", json={"progress": 1000})
    assert r2.status_code == 422
    assert r2.headers.get("content-type", "").startswith("application/problem+json")
    b2 = r2.json()
    assert b2["title"] == "Validation Error" and b2["status"] == 422
    assert isinstance(b2.get("errors"), list)
