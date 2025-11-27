from unittest.mock import patch
from fastapi.testclient import TestClient
from app.mardi_fdo_server import app

client = TestClient(app)

# Minimal publication Wikibase response
SAMPLE_PUBLICATION_ENTITY = {
    "labels": {"en": {"value": "Test Article"}},
    "descriptions": {"en": {"value": "A test publication"}},
    "claims": {
        "P31": [
            {  # instance of → ScholarlyArticle
                "mainsnak": {
                    "datavalue": {
                        "value": {"id": "Q56887"}
                    }
                }
            }
        ],
        # arXiv ID → ensures build_scholarly_article_profile creates encoding[] and pdf_url
        "P21": [
            {
                "mainsnak": {
                    "datavalue": {
                        "value": "2304.06137"
                    }
                }
            }
        ]
    },
    "modified": "2024-02-02T12:00:00Z"
}


@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_fdo_structure(mock_fetch):
    mock_fetch.return_value = SAMPLE_PUBLICATION_ENTITY

    resp = client.get("/fdo/Q111111")
    assert resp.status_code == 200
    data = resp.json()

    # top-level FDO
    assert data["@type"] == "DigitalObject"
    assert data["@id"] == "https://fdo.portal.mardi4nfdi.de/fdo/Q111111"

    # kernel
    kernel = data["kernel"]
    assert kernel["@id"] == data["@id"]
    assert kernel["digitalObjectType"] == "https://schema.org/ScholarlyArticle"
    assert kernel["primaryIdentifier"] == "mardi:Q111111"
    assert kernel["kernelVersion"] == "v1"
    assert kernel["immutable"] is True

    # Representation block
#    reps = kernel.get("fdo:hasRepresentation", [])
#    assert isinstance(reps, list)
#    assert len(reps) == 1
#    rep = reps[0]
#    assert rep["@id"] == "https://fdo.portal.mardi4nfdi.de/fdo/Q111111_FULLTEXT"
#    assert rep["mediaType"] == "application/pdf"

    # profile
    profile = data["profile"]
    assert profile["@type"] == "ScholarlyArticle"
    assert profile["@id"] == "https://portal.mardi4nfdi.de/entity/Q111111"
    assert profile["name"] == "Test Article"
    assert isinstance(profile["name"], str)

    # provenance
    prov = data["provenance"]
    assert "prov:generatedAtTime" in prov
    assert "prov:wasAttributedTo" in prov
