"""Shared test fixtures.

Link enrichment resolves referenced entities through ``fetch_entities``. Left
unpatched that reaches the live MediaWiki API, which would make the suite slow,
network-dependent and sensitive to real label changes. Every test therefore runs
with enrichment stubbed out to "resolves nothing", which is also the documented
degradation path: references fall back to bare ``@id``.

Tests that exercise enrichment patch ``app.mardi_fdo_server.fetch_entities``
themselves; the inner patch wins.
"""

from unittest.mock import patch

import pytest

import app.mardi_fdo_server as server


@pytest.fixture(autouse=True)
def no_network_link_enrichment():
    server.clear_link_cache()
    with patch.object(server, "fetch_entities", return_value={}):
        yield
    server.clear_link_cache()
