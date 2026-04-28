from unittest.mock import patch

from fastapi.testclient import TestClient

from app.mardi_fdo_server import app

client = TestClient(app)


def _p1827_claim(item_id: str, p1828: str) -> dict:
    return {
        "mainsnak": {
            "datavalue": {
                "type": "wikibase-entityid",
                "value": {"id": item_id},
            }
        },
        "qualifiers": {
            "P1828": [{"datavalue": {"type": "string", "value": p1828}}]
        },
    }


def _dataset_entity(p1827_claims=None, download_url=None):
    claims = {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q56885"}}}}]}
    if p1827_claims:
        claims["P1827"] = p1827_claims
    if download_url:
        claims["P205"] = [{"mainsnak": {"datavalue": {"value": download_url}}}]
    return {
        "labels": {"en": {"value": "Test Dataset"}},
        "descriptions": {},
        "claims": claims,
        "modified": "2026-01-01T00:00:00Z",
    }


def _publication_entity(p1827_claims=None, has_arxiv=True):
    claims = {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q56887"}}}}]}
    if has_arxiv:
        claims["P21"] = [{"mainsnak": {"datavalue": {"value": "2304.06137"}}}]
    if p1827_claims:
        claims["P1827"] = p1827_claims
    return {
        "labels": {"en": {"value": "Test Article"}},
        "descriptions": {},
        "claims": claims,
        "modified": "2026-01-01T00:00:00Z",
    }


def _software_application_entity(p1827_claims=None, download_url=None):
    claims = {
        "P1460": [
            {
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": "Q5976450"},
                    }
                }
            }
        ]
    }
    if download_url:
        claims["P205"] = [{"mainsnak": {"datavalue": {"value": download_url}}}]
    if p1827_claims:
        claims["P1827"] = p1827_claims
    return {
        "labels": {"en": {"value": "Test Software"}},
        "descriptions": {},
        "claims": claims,
        "modified": "2026-01-01T00:00:00Z",
    }


def _software_sourcecode_entity(p1827_claims=None, download_url=None, cran_name=None):
    claims = {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q57080"}}}}]}
    if download_url:
        claims["P205"] = [{"mainsnak": {"datavalue": {"value": download_url}}}]
    if cran_name:
        claims["P229"] = [{"mainsnak": {"datavalue": {"value": cran_name}}}]
    if p1827_claims:
        claims["P1827"] = p1827_claims
    return {
        "labels": {"en": {"value": "Test SourceCode"}},
        "descriptions": {},
        "claims": claims,
        "modified": "2026-01-01T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Exact P1828 → componentId naming (dataset as the base case)
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_p1828_extension_preserved(mock_fetch):
    mock_fetch.return_value = _dataset_entity([_p1827_claim("Q1", "documentation.pdf")])
    resp = client.get("/fdo/Q9001")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"]["fdo:hasComponent"]}
    assert "documentation.pdf" in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_p1828_no_extension_preserved(mock_fetch):
    mock_fetch.return_value = _dataset_entity([_p1827_claim("Q2", "documentation")])
    resp = client.get("/fdo/Q9002")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"]["fdo:hasComponent"]}
    assert "documentation" in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_p1828_multi_extension_preserved(mock_fetch):
    mock_fetch.return_value = _dataset_entity([_p1827_claim("Q3", "archive.tar.gz")])
    resp = client.get("/fdo/Q9003")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"]["fdo:hasComponent"]}
    assert "archive.tar.gz" in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_component_id_independent_of_media_type(mock_fetch):
    """componentId is the exact P1828 value; mediaType is derived independently and cannot alter it."""
    mock_fetch.return_value = _dataset_entity([_p1827_claim("Q4", "documentation.pdf")])
    resp = client.get("/fdo/Q9004")
    assert resp.status_code == 200
    components = resp.json()["kernel"]["fdo:hasComponent"]
    match = next(c for c in components if c["componentId"] == "documentation.pdf")
    assert match["componentId"] == "documentation.pdf"
    assert match["mediaType"] == "application/pdf"


# ---------------------------------------------------------------------------
# Dataset rocrate renamed to "rocrate.zip"
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_dataset_rocrate_component_id(mock_fetch):
    mock_fetch.return_value = _dataset_entity(download_url="https://example.org/dataset.zip")
    resp = client.get("/fdo/Q9020")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "rocrate.zip" in ids
    assert "rocrate" not in ids


# ---------------------------------------------------------------------------
# Publication fallback and P1828 override
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_fallback_fulltext_pdf(mock_fetch):
    """No P1828 present → falls back to 'fulltext.pdf'."""
    mock_fetch.return_value = _publication_entity(has_arxiv=True)
    resp = client.get("/fdo/Q9010")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "fulltext.pdf" in ids
    assert "fulltext" not in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_p1828_overrides_fallback(mock_fetch):
    """P1828 value is used; fallback is not added."""
    mock_fetch.return_value = _publication_entity(
        p1827_claims=[_p1827_claim("Q11", "article.pdf")],
        has_arxiv=True,
    )
    resp = client.get("/fdo/Q9011")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "article.pdf" in ids
    assert "fulltext.pdf" not in ids
    assert "fulltext" not in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_p1828_unrelated_suppresses_fulltext_fallback(mock_fetch):
    """A P1828 entry for a different artifact (e.g. supplement) suppresses the fulltext.pdf
    fallback. The contract is: if P1828 is used at all, it enumerates all components."""
    mock_fetch.return_value = _publication_entity(
        p1827_claims=[_p1827_claim("Q12", "supplement.csv")],
        has_arxiv=True,
    )
    resp = client.get("/fdo/Q9012")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "supplement.csv" in ids
    assert "fulltext.pdf" not in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_multiple_p1828_all_emitted(mock_fetch):
    """All P1828 entries are emitted as components."""
    mock_fetch.return_value = _publication_entity(
        p1827_claims=[
            _p1827_claim("Q13", "fulltext.pdf"),
            _p1827_claim("Q14", "supplement.csv"),
        ],
    )
    resp = client.get("/fdo/Q9013")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "fulltext.pdf" in ids
    assert "supplement.csv" in ids


# ---------------------------------------------------------------------------
# SoftwareApplication fallback and P1828 override
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_software_application_fallback(mock_fetch):
    """No P1828 → falls back to 'software-archive'."""
    mock_fetch.return_value = _software_application_entity(
        download_url="https://example.org/app.zip"
    )
    resp = client.get("/fdo/Q9030")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "software-archive" in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_software_application_p1828_overrides_fallback(mock_fetch):
    """P1828 value replaces fallback."""
    mock_fetch.return_value = _software_application_entity(
        p1827_claims=[_p1827_claim("Q31", "myapp.zip")],
    )
    resp = client.get("/fdo/Q9031")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "myapp.zip" in ids
    assert "software-archive" not in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_software_application_multiple_p1828_all_emitted(mock_fetch):
    """All P1828 entries are emitted; the software-archive fallback is suppressed."""
    mock_fetch.return_value = _software_application_entity(
        p1827_claims=[
            _p1827_claim("Q32", "app-linux.zip"),
            _p1827_claim("Q33", "app-windows.zip"),
        ],
        download_url="https://example.org/app.zip",
    )
    resp = client.get("/fdo/Q9032")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "app-linux.zip" in ids
    assert "app-windows.zip" in ids
    assert "software-archive" not in ids


# ---------------------------------------------------------------------------
# SoftwareSourceCode fallbacks and P1828 override
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_software_sourcecode_fallbacks(mock_fetch):
    """No P1828 → falls back to 'software-archive' and 'documentation.pdf'."""
    mock_fetch.return_value = _software_sourcecode_entity(
        download_url="https://example.org/pkg.tar.gz",
        cran_name="mypkg",
    )
    resp = client.get("/fdo/Q9040")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "software-archive" in ids
    assert "documentation.pdf" in ids
    assert "documentation" not in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_software_sourcecode_p1828_overrides_fallbacks(mock_fetch):
    """P1828 values replace all fallbacks."""
    mock_fetch.return_value = _software_sourcecode_entity(
        p1827_claims=[
            _p1827_claim("Q41", "source.tar.gz"),
            _p1827_claim("Q42", "manual.pdf"),
        ],
        download_url="https://example.org/pkg.tar.gz",
        cran_name="mypkg",
    )
    resp = client.get("/fdo/Q9041")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "source.tar.gz" in ids
    assert "manual.pdf" in ids
    assert "software-archive" not in ids
    assert "documentation.pdf" not in ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_software_sourcecode_single_p1828_suppresses_both_fallbacks(mock_fetch):
    """A single P1828 entry suppresses both the software-archive and documentation.pdf
    fallbacks. The contract is: if P1828 is used at all, it enumerates all components."""
    mock_fetch.return_value = _software_sourcecode_entity(
        p1827_claims=[_p1827_claim("Q43", "manual.pdf")],
        download_url="https://example.org/pkg.tar.gz",
        cran_name="mypkg",
    )
    resp = client.get("/fdo/Q9042")
    assert resp.status_code == 200
    ids = {c["componentId"] for c in resp.json()["kernel"].get("fdo:hasComponent", [])}
    assert "manual.pdf" in ids
    assert "software-archive" not in ids
    assert "documentation.pdf" not in ids
