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
    assert kernel["digitalObjectType"] == "https://fdo.portal.mardi4nfdi.de/fdo/types/ScholarlyArticle"
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


@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_has_part_single(mock_fetch):
    mock_fetch.return_value = {
        "labels": {"en": {"value": "Test Article"}},
        "descriptions": {"en": {"value": ""}},
        "claims": {
            "P31": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q56887"}}}}],
            "P1560": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q9001"}}}}],
        },
        "modified": "2024-01-01T00:00:00Z",
    }
    resp = client.get("/fdo/Q111112")
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["hasPart"] == [{"@id": "https://portal.mardi4nfdi.de/entity/Q9001"}]


@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_has_part_multiple(mock_fetch):
    mock_fetch.return_value = {
        "labels": {"en": {"value": "Test Article"}},
        "descriptions": {"en": {"value": ""}},
        "claims": {
            "P31": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q56887"}}}}],
            "P1560": [
                {"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q9001"}}}},
                {"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q9002"}}}},
            ],
        },
        "modified": "2024-01-01T00:00:00Z",
    }
    resp = client.get("/fdo/Q111113")
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["hasPart"] == [
        {"@id": "https://portal.mardi4nfdi.de/entity/Q9001"},
        {"@id": "https://portal.mardi4nfdi.de/entity/Q9002"},
    ]


_CITED_DATASET = {
    "labels": {"en": {"value": "RKI covid case numbers 03/2020 to 10/2020"}},
    "claims": {
        "P31": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q56885"}}}}]
    },
}
_CITED_CODE = {
    "labels": {"en": {"value": "Reproduce results from: Gaskin, Conrad et al. (2024); figure 3"}},
    "claims": {
        "P1460": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q6534216"}}}}]
    },
}


def _article_citing(*qids):
    return {
        "labels": {"en": {"value": "Test Article"}},
        "descriptions": {"en": {"value": ""}},
        "claims": {
            "P31": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q56887"}}}}],
            "P223": [
                {"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": q}}}}
                for q in qids
            ],
        },
        "modified": "2024-01-01T00:00:00Z",
    }


@patch(
    "app.mardi_fdo_server.fetch_entities",
    return_value={"Q6830878": _CITED_DATASET, "Q6830877": _CITED_CODE},
)
@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_citation_enriched(mock_fetch, mock_batch):
    """P223 (cites work) carries @type and name, so a client can tell code from data."""
    mock_fetch.return_value = _article_citing("Q6830878", "Q6830877")

    resp = client.get("/fdo/Q6830876")
    assert resp.status_code == 200
    citation = resp.json()["profile"]["citation"]

    assert citation == [
        {
            "@id": "https://portal.mardi4nfdi.de/entity/Q6830878",
            "@type": "Dataset",
            "name": "RKI covid case numbers 03/2020 to 10/2020",
        },
        {
            "@id": "https://portal.mardi4nfdi.de/entity/Q6830877",
            "@type": "Workflow",
            "name": "Reproduce results from: Gaskin, Conrad et al. (2024); figure 3",
        },
    ]
    # Both references resolved in a single batched lookup.
    assert mock_batch.call_count == 1
    assert sorted(mock_batch.call_args[0][0]) == ["Q6830877", "Q6830878"]


@patch("app.mardi_fdo_server.fetch_entities", return_value={})
@patch("app.mardi_fdo_server.fetch_entity")
def test_publication_citation_bare_when_unresolvable(mock_fetch, _mock_batch):
    """An unresolved reference keeps its @id rather than being dropped."""
    mock_fetch.return_value = _article_citing("Q6830878")

    resp = client.get("/fdo/Q6830876")
    assert resp.status_code == 200
    assert resp.json()["profile"]["citation"] == [
        {"@id": "https://portal.mardi4nfdi.de/entity/Q6830878"}
    ]
