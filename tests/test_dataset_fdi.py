from unittest.mock import patch

from fastapi.testclient import TestClient

from app.mardi_fdo_server import app

client = TestClient(app)


SAMPLE_DATASET_ENTITY = {
    "labels": {
        "en": {
            "value": "RKI covid case numbers 03/2020 to 10/2020"
        }
    },
    "descriptions": {},
    "claims": {
        "P31": [
            {
                "mainsnak": {
                    "datavalue": {
                        "value": {"id": "Q56885"}
                    }
                }
            }
        ],
        "P1827": [
            {
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": "Q6830870"}
                    }
                },
                "qualifiers": {
                    "P1828": [
                        {
                            "datavalue": {
                                "type": "string",
                                "value": "rki_corona_cases_2020.csv"
                            }
                        }
                    ]
                }
            }
        ]
    },
    "modified": "2026-04-07T15:44:34Z"
}


@patch("app.mardi_fdo_server.fetch_entity")
def test_dataset_components_from_storage_qualifiers(mock_fetch):
    mock_fetch.return_value = SAMPLE_DATASET_ENTITY

    resp = client.get("/fdo/Q6830878")
    assert resp.status_code == 200

    data = resp.json()
    assert data["@type"] == "DigitalObject"
    assert data["kernel"]["digitalObjectType"] == "https://schema.org/Dataset"

    components = data["kernel"].get("fdo:hasComponent", [])
    component_ids = {component["componentId"] for component in components}

    assert "software-archive" in component_ids
    assert "fulltext" not in component_ids
