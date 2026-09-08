"""Tests for applicableOperations on type FDOs.

applicableOperations is a statement about the type, not a promise by a server:
a DOIP service intersects it with the operations it implements. These tests lock
the invariants that make that safe.
"""

import pytest
from fastapi.testclient import TestClient

from app.mardi_fdo_server import app
from app.type_registry import TYPE_REGISTRY

client = TestClient(app)

# Operations addressed to the service itself, never to a digital object.
SERVICE_LEVEL = {
    "0.DOIP/Op.Hello",
    "0.DOIP/Op.ListOperations",
    "0.DOIP/Op.Create",
    "0.DOIP/Op.Search",
}


def test_every_type_declares_applicable_operations():
    for type_id, entry in TYPE_REGISTRY.items():
        ops = entry.get("applicableOperations")
        assert ops, f"{type_id} declares no applicableOperations"


@pytest.mark.parametrize("type_id", sorted(TYPE_REGISTRY))
def test_identifiers_are_namespaced(type_id):
    for op in TYPE_REGISTRY[type_id]["applicableOperations"]:
        assert op.startswith(("0.DOIP/Op.", "0.MaRDI/Op.")), f"{type_id}: {op}"


@pytest.mark.parametrize("type_id", sorted(TYPE_REGISTRY))
def test_no_service_level_operation_is_declared_on_a_type(type_id):
    """Create/Search/Hello/ListOperations address the service, not an object."""
    declared = set(TYPE_REGISTRY[type_id]["applicableOperations"])
    assert not (declared & SERVICE_LEVEL), f"{type_id} declares service-level ops"


@pytest.mark.parametrize("type_id", sorted(TYPE_REGISTRY))
def test_no_duplicates(type_id):
    ops = TYPE_REGISTRY[type_id]["applicableOperations"]
    assert len(ops) == len(set(ops))


def test_retrieve_is_applicable_to_every_type():
    for type_id, entry in TYPE_REGISTRY.items():
        assert "0.DOIP/Op.Retrieve" in entry["applicableOperations"], type_id


def test_invoke_is_declared_only_where_a_workflow_exists():
    """equation_extraction reads primary.pdf, so it is article-specific."""
    for type_id, entry in TYPE_REGISTRY.items():
        if "0.MaRDI/Op.Invoke" in entry["applicableOperations"]:
            assert type_id == "ScholarlyArticle", type_id


@pytest.mark.parametrize("type_id", sorted(TYPE_REGISTRY))
def test_endpoint_serves_applicable_operations(type_id):
    r = client.get(f"/fdo/types/{type_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["applicableOperations"] == TYPE_REGISTRY[type_id]["applicableOperations"]


def test_object_fdo_carries_no_operations_list():
    """Operations live on the type; objects carry only digitalObjectType."""
    for type_id in TYPE_REGISTRY:
        body = client.get(f"/fdo/types/{type_id}").json()
        assert "applicableOperations" not in body["kernel"]
