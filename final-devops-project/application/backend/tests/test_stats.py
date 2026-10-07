def test_stats_summarise_one_day(client, book, doctor_id):
    first = book("2026-10-08T09:00").json()
    book("2026-10-08T09:30", phone="+91 90000 22222")
    third = book("2026-10-08T10:00", phone="+91 90000 33333").json()
    book("2026-10-09T09:00", phone="+91 90000 44444")  # different day
    client.put(f"/api/appointments/{first['id']}", json={"status": "COMPLETED"})
    client.post(f"/api/appointments/{third['id']}/cancel")

    stats = client.get("/api/stats", params={"on": "2026-10-08"}).json()
    assert stats["date"] == "2026-10-08"
    assert (stats["total"], stats["scheduled"], stats["completed"], stats["cancelled"]) == (3, 1, 1, 1)
    assert stats["patients"] == 4
    assert stats["active_doctors"] == 2
    assert stats["upcoming_7_days"] == 2  # one scheduled on the 8th + one on the 9th

    load = {d["doctor_id"]: d for d in stats["by_doctor"]}
    assert load[doctor_id]["booked"] == 2  # the cancelled slot is not counted as load
    assert load[doctor_id]["booked_minutes"] == 60
    assert sum(d["booked"] for d in stats["by_doctor"]) == 2  # nobody else has bookings


def test_stats_default_to_today(client):
    stats = client.get("/api/stats").json()
    assert stats["total"] == 0
    assert len(stats["by_doctor"]) == 2
