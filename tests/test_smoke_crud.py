def test_crud_happy(client):
    created = client.post("/topics", json={"title": "P05", "deadline": None}).json()
    tid = created["id"]

    got = client.get(f"/topics/{tid}").json()
    assert got["title"] == "P05"

    upd = client.put(f"/topics/{tid}/progress", json={"progress": 40})
    assert upd.status_code == 200

    deleted = client.delete(f"/topics/{tid}")
    assert deleted.status_code == 200
