"""Platform endpoints used by Docker/Kubernetes probes and Prometheus."""


def test_root_describes_service(client):
    body = client.get("/").json()
    assert body["service"] == "ClinicDesk API"
    assert body["docs"] == "/docs"


def test_health_is_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY", "database": "ok"}


def test_metrics_exposes_prometheus_format(client):
    client.get("/api/doctors")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert 'handler="/api/doctors"' in response.text


def test_openapi_lists_core_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/api/appointments", "/api/appointments/{appointment_id}", "/api/doctors", "/api/stats"):
        assert path in paths
