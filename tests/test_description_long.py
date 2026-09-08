"""Tests for the MaRDI-namespaced long description.

P1459 ("Description (long)") has no schema.org equivalent. It is emitted as
mardi:descriptionLong rather than squeezed into `description` (which already
carries the wiki description field, and the two co-occur) or `abstract` (which
a publication's real abstract should keep).
"""

import pytest
from fastapi.testclient import TestClient

from app.fdo_config import MARDI_NS, PROFILE_CONTEXT
from app.mardi_fdo_server import app
from app.type_registry import TYPE_REGISTRY

client = TestClient(app)

# Every type whose builder reads P1459.
TYPES_WITH_LONG_DESCRIPTION = [
    "ScholarlyArticle", "Dataset", "Workflow",
    "SoftwareApplication", "SoftwareSourceCode", "Formula",
]


def test_profile_context_declares_the_mardi_prefix():
    assert PROFILE_CONTEXT[0] == "https://schema.org/"
    assert PROFILE_CONTEXT[1]["mardi"] == MARDI_NS
    assert MARDI_NS.endswith("/"), "prefix must end in / so terms concatenate"


@pytest.mark.parametrize("type_id", TYPES_WITH_LONG_DESCRIPTION)
def test_type_advertises_the_namespaced_field(type_id):
    m = TYPE_REGISTRY[type_id]["propertyMappings"]
    hits = [k for k, v in m.items() if v["pid"] == "P1459"]
    assert hits == ["mardi:descriptionLong"], f"{type_id}: {hits}"


def test_person_does_not_map_it():
    """No Person item carries P1459; do not advertise a mapping we never emit."""
    m = TYPE_REGISTRY["Person"]["propertyMappings"]
    assert not [k for k, v in m.items() if v["pid"] == "P1459"]


def test_no_type_still_advertises_the_old_unqualified_name():
    """description_long is not a schema.org term - a JSON-LD processor drops it."""
    for type_id, entry in TYPE_REGISTRY.items():
        assert "description_long" not in entry["propertyMappings"], type_id


@pytest.mark.parametrize("type_id", sorted(TYPE_REGISTRY))
def test_every_mapped_field_is_schema_org_or_namespaced(type_id):
    """A profile key is either a schema.org term or explicitly mardi:-prefixed."""
    for field in TYPE_REGISTRY[type_id]["propertyMappings"]:
        if field.startswith("mardi:"):
            continue
        assert "_" not in field, (
            f"{type_id}.{field}: snake_case is not a schema.org term; "
            "namespace it as mardi: or use the schema.org spelling"
        )


@pytest.mark.parametrize("type_id", sorted(TYPE_REGISTRY))
def test_type_endpoint_serves_the_mapping(type_id):
    body = client.get(f"/fdo/types/{type_id}").json()
    assert body["propertyMappings"] == TYPE_REGISTRY[type_id]["propertyMappings"]
