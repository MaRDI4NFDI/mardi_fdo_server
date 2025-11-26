"""
Basic integration tests for the MaRDI FDO FastAPI prototype.
"""

from fastapi.testclient import TestClient

from app.mardi_fdo_server import app

client = TestClient(app)


def test_health_endpoint():
    """Service exposes a healthy status endpoint."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_invalid_qid():
    """Requests must use Q-prefixed identifiers."""
    resp = client.get("/fdo/abc")
    assert resp.status_code == 400

"""
Bitstream FDO: malformed identifier rejection tests.
"""
from fastapi.testclient import TestClient
from app.mardi_fdo_server import app

client = TestClient(app)


"""
Negative Test for Bad Bitstream IDs
"""
def test_bitstream_invalid_id_rejected():
    bad_ids = [
        "/fdo/X123_FULLTEXT",
        "/fdo/QABC_FULLTEXT",
        "/fdo/Q123_FULLTEX",
        "/fdo/Q_FULLTEXT",
    ]

    for path in bad_ids:
        resp = client.get(path)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid FDO identifier"
