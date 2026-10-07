def test_list_doctors_hides_inactive_by_default(client):
    names = [d["full_name"] for d in client.get("/api/doctors").json()]
    assert "Dr. Test Physician" in names
    assert "Dr. On Leave" not in names

    all_names = [d["full_name"] for d in client.get("/api/doctors?include_inactive=true").json()]
    assert "Dr. On Leave" in all_names


def test_create_and_fetch_doctor(client):
    created = client.post("/api/doctors", json={"full_name": "Dr. Kavya Menon", "specialty": "ENT", "room": "2-03"})
    assert created.status_code == 201
    doctor_id = created.json()["id"]
    assert client.get(f"/api/doctors/{doctor_id}").json()["specialty"] == "ENT"
    assert client.get("/api/doctors/9999").status_code == 404


def test_create_patient_and_reject_duplicate_phone(client):
    payload = {"full_name": "Arjun Das", "phone": "+91 90000 11111", "email": "arjun@example.com"}
    assert client.post("/api/patients", json=payload).status_code == 201
    assert client.post("/api/patients", json=payload).status_code == 409
    found = client.get("/api/patients", params={"q": "Arjun"}).json()
    assert [p["phone"] for p in found] == ["+91 90000 11111"]


def test_patient_phone_is_validated(client):
    response = client.post("/api/patients", json={"full_name": "Bad Phone", "phone": "call me"})
    assert response.status_code == 422
