def test_book_appointment_registers_walk_in_patient(client, book):
    response = book()
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SCHEDULED"
    assert body["patient"]["full_name"] == "Priya Nair"
    assert body["scheduled_at"] == "2026-10-08T10:00:00"
    assert body["ends_at"] == "2026-10-08T10:30:00"
    assert len(client.get("/api/patients").json()) == 1


def test_book_with_existing_patient_id(client, doctor_id):
    patient = client.post("/api/patients", json={"full_name": "Meera Joshi", "phone": "9123456789"}).json()
    response = client.post(
        "/api/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient["id"], "scheduled_at": "2026-10-08T09:00"},
    )
    assert response.status_code == 201
    assert response.json()["patient"]["id"] == patient["id"]
    assert response.json()["duration_minutes"] == 30


def test_booking_requires_exactly_one_patient_reference(client, doctor_id):
    response = client.post("/api/appointments", json={"doctor_id": doctor_id, "scheduled_at": "2026-10-08T09:00"})
    assert response.status_code == 422


def test_unknown_or_inactive_doctor_cannot_be_booked(client, book):
    assert book(doctor=9999).status_code == 404
    inactive = next(d for d in client.get("/api/doctors?include_inactive=true").json() if not d["active"])
    assert book(doctor=inactive["id"]).status_code == 422


def test_double_booking_same_doctor_is_rejected(client, book):
    assert book("2026-10-08T10:00", 30).status_code == 201
    clash = book("2026-10-08T10:15", 30, phone="+91 99999 00000", name="Rahul Sen")
    assert clash.status_code == 409
    assert "10:00 to 10:30" in clash.json()["detail"]


def test_back_to_back_slots_are_allowed(client, book):
    assert book("2026-10-08T10:00", 30).status_code == 201
    assert book("2026-10-08T10:30", 30, phone="+91 99999 00000").status_code == 201


def test_update_status_and_reschedule(client, book):
    appt_id = book("2026-10-08T11:00").json()["id"]
    checked_in = client.put(f"/api/appointments/{appt_id}", json={"status": "CHECKED_IN", "notes": "BP 120/80"})
    assert checked_in.status_code == 200
    assert checked_in.json()["status"] == "CHECKED_IN"

    moved = client.put(f"/api/appointments/{appt_id}", json={"scheduled_at": "2026-10-08T12:00", "duration_minutes": 45})
    assert moved.json()["ends_at"] == "2026-10-08T12:45:00"


def test_reschedule_into_taken_slot_is_rejected(client, book):
    book("2026-10-08T15:00")
    second = book("2026-10-08T16:00", phone="+91 99999 00000").json()["id"]
    response = client.put(f"/api/appointments/{second}", json={"scheduled_at": "2026-10-08T15:15"})
    assert response.status_code == 409


def test_cancel_frees_the_slot_and_locks_the_record(client, book):
    appt_id = book("2026-10-08T10:00").json()["id"]
    cancelled = client.post(f"/api/appointments/{appt_id}/cancel")
    assert cancelled.json()["status"] == "CANCELLED"
    assert client.post(f"/api/appointments/{appt_id}/cancel").status_code == 409
    assert client.put(f"/api/appointments/{appt_id}", json={"status": "SCHEDULED"}).status_code == 409
    # the same slot can now be given to someone else
    assert book("2026-10-08T10:00", phone="+91 99999 00000").status_code == 201


def test_list_filters_by_date_and_status(client, book):
    book("2026-10-08T10:00")
    other_day = book("2026-10-09T10:00").json()["id"]
    client.post(f"/api/appointments/{other_day}/cancel")

    on_8th = client.get("/api/appointments", params={"on": "2026-10-08"}).json()
    assert [a["scheduled_at"][:10] for a in on_8th] == ["2026-10-08"]
    cancelled = client.get("/api/appointments", params={"status": "CANCELLED"}).json()
    assert [a["id"] for a in cancelled] == [other_day]
    assert client.get("/api/appointments", params={"status": "LOST"}).status_code == 422


def test_delete_appointment(client, book):
    appt_id = book().json()["id"]
    assert client.delete(f"/api/appointments/{appt_id}").status_code == 204
    assert client.get(f"/api/appointments/{appt_id}").status_code == 404


def test_duration_bounds_are_enforced(client, book):
    assert book(minutes=5).status_code == 422
    assert book(minutes=180).status_code == 422
