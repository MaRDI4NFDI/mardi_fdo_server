from unittest.mock import patch

from fastapi.testclient import TestClient

from app.mardi_fdo_server import app

client = TestClient(app)


def _workflow_entity_p31(extra_claims=None):
    """Minimal workflow entity typed via P31 (instance of Q68657)."""
    claims = {
        "P31": [
            {
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": "Q68657"},
                    }
                }
            }
        ]
    }
    if extra_claims:
        claims.update(extra_claims)
    return {
        "labels": {"en": {"value": "My Snakemake Workflow"}},
        "descriptions": {"en": {"value": "A test workflow"}},
        "claims": claims,
        "modified": "2026-04-08T10:00:00Z",
    }


def _workflow_entity_p1460(extra_claims=None):
    """Minimal workflow entity typed via P1460 (MaRDI profile type Q6534216)."""
    claims = {
        "P1460": [
            {
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": "Q6534216"},
                    }
                }
            }
        ]
    }
    if extra_claims:
        claims.update(extra_claims)
    return {
        "labels": {"en": {"value": "My Nextflow Workflow"}},
        "descriptions": {},
        "claims": claims,
        "modified": "2026-04-08T10:00:00Z",
    }


def _p1827_entry(item_id, qualifiers):
    """Build a single P1827 'stored at' statement with the given qualifiers."""
    qualifier_block = {}
    for prop, value in qualifiers.items():
        qualifier_block[prop] = [
            {"datavalue": {"type": "string", "value": value}}
        ]
    return {
        "mainsnak": {
            "datavalue": {
                "type": "wikibase-entityid",
                "value": {"id": item_id},
            }
        },
        "qualifiers": qualifier_block,
    }


# ---------------------------------------------------------------------------
# Type routing
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_type_routing_via_p31(mock_fetch):
    mock_fetch.return_value = _workflow_entity_p31()

    resp = client.get("/fdo/Q9000001")
    assert resp.status_code == 200

    data = resp.json()
    assert data["@type"] == "DigitalObject"
    assert data["kernel"]["digitalObjectType"] == "https://fdo.portal.mardi4nfdi.de/fdo/types/Workflow"


@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_type_routing_via_p1460(mock_fetch):
    mock_fetch.return_value = _workflow_entity_p1460()

    resp = client.get("/fdo/Q9000002")
    assert resp.status_code == 200

    data = resp.json()
    assert data["kernel"]["digitalObjectType"] == "https://fdo.portal.mardi4nfdi.de/fdo/types/Workflow"


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_component_from_p1828(mock_fetch):
    """P1827 entry with a P1828 qualifier creates a kernel component."""
    entity = _workflow_entity_p31({
        "P1827": [_p1827_entry("Q1001", {"P1828": "workflow.cwl"})]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000003")
    assert resp.status_code == 200

    components = resp.json()["kernel"].get("fdo:hasComponent", [])
    component_ids = {c["componentId"] for c in components}
    assert "workflow.cwl" in component_ids


@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_no_components_without_p1828(mock_fetch):
    """P1827 entries lacking P1828 do not produce kernel components."""
    entity = _workflow_entity_p31({
        "P1827": [_p1827_entry("Q1003", {"P188": "https://example.org/workflow.cwl"})]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000005")
    assert resp.status_code == 200

    components = resp.json()["kernel"].get("fdo:hasComponent", [])
    assert components == []


# ---------------------------------------------------------------------------
# Distributions
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_distributions_from_qualifier_urls(mock_fetch):
    """P188 / P205 / P504 qualifier URLs appear in profile.distribution."""
    entity = _workflow_entity_p31({
        "P1827": [
            _p1827_entry("Q1004", {"P188": "https://example.org/workflow.cwl"}),
            _p1827_entry("Q1005", {"P205": "https://example.org/workflow.zip"}),
            _p1827_entry("Q1006", {"P504": "https://example.org/workflow.tar.gz"}),
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000006")
    assert resp.status_code == 200

    distributions = resp.json()["profile"].get("distribution", [])
    distribution_urls = {d["contentUrl"] for d in distributions}
    assert "https://example.org/workflow.cwl" in distribution_urls
    assert "https://example.org/workflow.zip" in distribution_urls
    assert "https://example.org/workflow.tar.gz" in distribution_urls


@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_p1828_component_gets_doip_distribution(mock_fetch):
    """A P1828 component also gets a DOIP retrieve URL in profile.distribution."""
    entity = _workflow_entity_p31({
        "P1827": [_p1827_entry("Q1007", {"P1828": "workflow.cwl"})]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000007")
    assert resp.status_code == 200

    distributions = resp.json()["profile"].get("distribution", [])
    distribution_urls = {d["contentUrl"] for d in distributions}
    assert "https://doip.portal.mardi4nfdi.de/doip/retrieve/Q9000007/workflow.cwl" in distribution_urls


@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_mixed_storage_qualifiers(mock_fetch):
    """P1828 entries become components; P188/P205/P504 entries become distributions only."""
    entity = _workflow_entity_p31({
        "P1827": [
            _p1827_entry("Q1008", {"P1828": "pipeline.nf"}),
            _p1827_entry("Q1009", {"P188": "https://github.com/org/repo/archive/main.zip"}),
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000008")
    assert resp.status_code == 200

    data = resp.json()
    components = data["kernel"].get("fdo:hasComponent", [])
    component_ids = {c["componentId"] for c in components}
    distributions = data["profile"].get("distribution", [])
    distribution_urls = {d["contentUrl"] for d in distributions}

    assert "pipeline.nf" in component_ids
    assert "https://github.com/org/repo/archive/main.zip" not in component_ids
    assert "https://github.com/org/repo/archive/main.zip" in distribution_urls


@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_duplicate_distribution_urls_deduplicated(mock_fetch):
    """The same URL appearing in multiple P1827 qualifier entries is only emitted once."""
    shared_url = "https://example.org/workflow.cwl"
    entity = _workflow_entity_p31({
        "P1827": [
            _p1827_entry("Q1010", {"P188": shared_url}),
            _p1827_entry("Q1011", {"P205": shared_url}),
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000009")
    assert resp.status_code == 200

    distributions = resp.json()["profile"].get("distribution", [])
    urls = [d["contentUrl"] for d in distributions]
    assert urls.count(shared_url) == 1


# ---------------------------------------------------------------------------
# Profile fields
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_zenodo_same_as(mock_fetch):
    """P227 (Zenodo record id) is added to profile.sameAs."""
    entity = _workflow_entity_p31({
        "P227": [
            {
                "mainsnak": {
                    "datavalue": {"type": "string", "value": "12345678"}
                }
            }
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9000010")
    assert resp.status_code == 200

    same_as = resp.json()["profile"].get("sameAs", [])
    assert "https://zenodo.org/record/12345678" in same_as


@patch("app.mardi_fdo_server.fetch_entity")
def test_workflow_profile_base_fields(mock_fetch):
    mock_fetch.return_value = _workflow_entity_p31()

    resp = client.get("/fdo/Q9000011")
    assert resp.status_code == 200

    profile = resp.json()["profile"]
    assert profile["@type"] == "Workflow"
    assert profile["name"] == "My Snakemake Workflow"
    assert profile["description"] == "A test workflow"
    assert "doi" not in str(profile)
