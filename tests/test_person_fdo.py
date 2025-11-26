"""
Tests for the Author/Person FDO schema.
"""
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.mardi_fdo_server import app

client = TestClient(app)

# Sample minimal Wikibase response for a Person (based on Q57162 structure)
SAMPLE_PERSON_ENTITY = {
    "labels": {"en": {"value": "Test Author"}},
    "descriptions": {"en": {"value": "A test researcher"}},
    "claims": {
        "P31": [  # instance of
            {
                "mainsnak": {
                    "datavalue": {
                        "value": {"id": "Q57162"}  # Author/Person type
                    }
                }
            }
        ],
        "P1416": [  # affiliation
            {
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": "Q123"}
                    }
                }
            }
        ],
        "P856": [  # official website
            {
                "mainsnak": {
                    "datavalue": {
                        "value": "https://example.com"
                    }
                }
            }
        ],
        "P496": [  # ORCID
            {
                "mainsnak": {
                    "datavalue": {
                        "value": "0000-0000-0000-0000"
                    }
                }
            }
        ]
    },
    "modified": "2023-01-01T00:00:00Z"
}

@patch("app.mardi_fdo_server.fetch_entity")
def test_author_fdo_structure(mock_fetch):
    mock_fetch.return_value = SAMPLE_PERSON_ENTITY

    resp = client.get("/fdo/Q999999")
    assert resp.status_code == 200
    data = resp.json()

    # top-level FDO
    assert data["@type"] == "schema:Person"
    assert data["@id"] == "https://fdo.portal.mardi4nfdi.de/fdo/Q999999"

    # kernel
    kernel = data["kernel"]
    assert kernel["@id"] == data["@id"]
    assert kernel["digitalObjectType"] == "https://schema.org/Person"
    assert kernel["primaryIdentifier"] == "mardi:Q999999"
    assert kernel["kernelVersion"] == "v1"
    assert kernel["immutable"] is True

    # profile
    profile = data["profile"]
    assert profile["@type"] == "Person"
    assert profile["@id"] == "https://portal.mardi4nfdi.de/entity/Q999999"
    assert profile["name"] == "Test Author"
    assert isinstance(profile["name"], str)

    # provenance
    prov = data["provenance"]
    assert "prov:generatedAtTime" in prov
    assert "prov:wasAttributedTo" in prov
