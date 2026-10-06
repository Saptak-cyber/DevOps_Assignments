import json
import os
import sys
import threading
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.server import calculate, make_server


@pytest.fixture(scope="module")
def base_url():
    server = make_server(host="127.0.0.1", port=0)   # port 0 = pick a free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def get(url):
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def test_calculate_function():
    assert calculate("10", "5", "multiply") == 50


def test_calculate_unknown_op():
    with pytest.raises(ValueError):
        calculate(1, 2, "power")


def test_health(base_url):
    assert get(f"{base_url}/health") == (200, {"status": "ok"})


def test_calculate_endpoint(base_url):
    status, body = get(f"{base_url}/calculate?a=10&b=5&op=add")
    assert status == 200
    assert body["result"] == 15


def test_divide_by_zero_endpoint(base_url):
    status, body = get(f"{base_url}/calculate?a=10&b=0&op=divide")
    assert status == 400
    assert "zero" in body["error"]


def test_missing_params(base_url):
    status, _ = get(f"{base_url}/calculate?a=1")
    assert status == 400


def test_not_found(base_url):
    status, _ = get(f"{base_url}/nope")
    assert status == 404
