"""Tests for the linked-entity cache used by reference enrichment."""

from unittest.mock import patch

import pytest

import app.mardi_fdo_server as server

# Captured at import, before conftest's autouse fixture stubs enrichment out:
# these tests exercise the real implementation.
fetch_entities = server.fetch_entities


class _Response:
    def __init__(self, ids: str):
        self._ids = ids

    def raise_for_status(self):
        pass

    def json(self):
        return {"entities": {q: {"labels": {"en": {"value": q}}} for q in self._ids.split("|")}}


@pytest.fixture
def live_cache():
    """Start and end each test with an empty linked-entity cache."""
    server.clear_link_cache()
    yield
    server.clear_link_cache()


def test_entities_are_cached_individually_not_per_batch(live_cache):
    """An entity reached from several records is fetched once."""
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(params["ids"])
        return _Response(params["ids"])

    with patch.object(server.httpx, "get", fake_get):
        fetch_entities(["Q1", "Q2"])
        fetch_entities(["Q2", "Q3"])        # Q2 already resolved
        fetch_entities(["Q1", "Q2", "Q3"])  # all resolved

    assert calls == ["Q1|Q2", "Q3"]


def test_failed_lookup_is_not_cached(live_cache):
    """A transient backend error must not permanently strip enrichment."""
    attempts = []

    def flaky_get(url, params=None, timeout=None):
        attempts.append(params["ids"])
        if len(attempts) == 1:
            raise RuntimeError("transient blip")
        return _Response(params["ids"])

    with patch.object(server.httpx, "get", flaky_get):
        first = fetch_entities(["Q1"])
        retry = fetch_entities(["Q1"])

    assert first == {}
    assert list(retry) == ["Q1"]
    assert len(attempts) == 2


def test_cache_entries_expire(live_cache, monkeypatch):
    """A stale entry is refetched, so an edited label eventually propagates."""
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(params["ids"])
        return _Response(params["ids"])

    with patch.object(server.httpx, "get", fake_get):
        fetch_entities(["Q9"])
        monkeypatch.setattr(server, "LINK_CACHE_TTL_SECONDS", -1)
        fetch_entities(["Q9"])

    assert calls == ["Q9", "Q9"]


def test_missing_entity_is_not_cached(live_cache):
    """A QID the backend reports as missing yields nothing and is not stored."""

    class _Missing:
        def raise_for_status(self):
            pass

        def json(self):
            return {"entities": {"Q404": {"missing": ""}}}

    with patch.object(server.httpx, "get", lambda url, params=None, timeout=None: _Missing()):
        assert fetch_entities(["Q404"]) == {}

    assert server._link_cache == {}


def test_batches_respect_the_api_limit(live_cache):
    """More than 50 links are split across requests rather than one huge call."""
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(params["ids"])
        return _Response(params["ids"])

    ids = [f"Q{i}" for i in range(120)]
    with patch.object(server.httpx, "get", fake_get):
        fetch_entities(ids)

    assert len(calls) == 3
    assert all(len(c.split("|")) <= server.MW_IDS_PER_REQUEST for c in calls)


def test_type_fdo_declares_which_fields_are_enriched():
    """A client can discover enrichment from the type FDO, not by trial and error."""
    from fastapi.testclient import TestClient

    mappings = TestClient(server.app).get("/fdo/types/ScholarlyArticle").json()["propertyMappings"]

    assert mappings["citation"]["embed"] == ["@type", "name"]
    assert mappings["hasPart"]["embed"] == ["@type", "name"]
    # Not every item reference is enriched, and the mapping says so by omission.
    assert "embed" not in mappings["author"]
    assert "embed" not in mappings["license"]


def test_enrichment_follows_the_registry(live_cache, monkeypatch):
    """Removing 'embed' from a mapping turns that field back into bare references."""
    from app.mardi_item_helper import refs_for_field
    from app.type_registry import TYPE_REGISTRY

    ids = ["Q1"]
    fetch = lambda qids: {"Q1": {"labels": {"en": {"value": "One"}}, "claims": {}}}

    assert refs_for_field("ScholarlyArticle", "citation", ids, fetch)[0].get("name") == "One"

    patched = dict(TYPE_REGISTRY["ScholarlyArticle"]["propertyMappings"])
    patched["citation"] = {k: v for k, v in patched["citation"].items() if k != "embed"}
    monkeypatch.setitem(TYPE_REGISTRY, "ScholarlyArticle",
                        {**TYPE_REGISTRY["ScholarlyArticle"], "propertyMappings": patched})

    assert refs_for_field("ScholarlyArticle", "citation", ids, fetch) == [
        {"@id": "https://portal.mardi4nfdi.de/entity/Q1"}
    ]
