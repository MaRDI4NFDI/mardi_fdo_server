from unittest.mock import patch

from fastapi.testclient import TestClient

from app.mardi_fdo_server import app

client = TestClient(app)


def _formula_entity_p1460(extra_claims=None):
    """Minimal formula entity typed via P1460=Q5981696."""
    claims = {
        "P1460": [
            {
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": "Q5981696"},
                    }
                }
            }
        ]
    }
    if extra_claims:
        claims.update(extra_claims)
    return {
        "labels": {"en": {"value": "Gamma function"}},
        "descriptions": {"en": {"value": "Extension of the factorial"}},
        "claims": claims,
        "modified": "2026-06-01T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Type routing
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_type_routing_via_p1460(mock_fetch):
    mock_fetch.return_value = _formula_entity_p1460()

    resp = client.get("/fdo/Q9990001")
    assert resp.status_code == 200

    data = resp.json()
    assert data["@type"] == "DigitalObject"
    assert data["kernel"]["digitalObjectType"] == "https://fdo.portal.mardi4nfdi.de/fdo/types/Formula"
    assert data["kernel"]["seeAlso"] == "https://schema.org/Formula"


# ---------------------------------------------------------------------------
# Profile base fields
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_profile_base_fields(mock_fetch):
    mock_fetch.return_value = _formula_entity_p1460()

    resp = client.get("/fdo/Q9990002")
    assert resp.status_code == 200

    profile = resp.json()["profile"]
    assert profile["@type"] == "Formula"
    assert profile["name"] == "Gamma function"
    assert profile["description"] == "Extension of the factorial"


# ---------------------------------------------------------------------------
# mathExpression: P989 preferred over P14
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_math_expression_p989(mock_fetch):
    entity = _formula_entity_p1460({
        "P989": [{"mainsnak": {"datavalue": {"type": "string", "value": "\\Gamma(z)"}}}],
        "P14":  [{"mainsnak": {"datavalue": {"type": "string", "value": "\\Gamma(z)_dlmf"}}}],
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990003")
    profile = resp.json()["profile"]
    assert profile["mathExpression"] == "\\Gamma(z)"


@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_math_expression_p14_fallback(mock_fetch):
    entity = _formula_entity_p1460({
        "P14": [{"mainsnak": {"datavalue": {"type": "string", "value": "\\deriv{f}{x}"}}}],
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990004")
    profile = resp.json()["profile"]
    assert profile["mathExpression"] == "\\deriv{f}{x}"


# ---------------------------------------------------------------------------
# Symbols
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_p983_symbols(mock_fetch):
    """P983 symbols appear in profile.symbol with optional represents."""
    entity = _formula_entity_p1460({
        "P983": [
            {
                "mainsnak": {"datavalue": {"type": "string", "value": "H"}},
                "qualifiers": {
                    "P984": [{"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q6534301"}}}]
                },
            }
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990005")
    symbols = resp.json()["profile"]["symbol"]
    assert len(symbols) == 1
    assert symbols[0]["notation"] == "H"
    assert symbols[0]["represents"]["@id"] == "https://portal.mardi4nfdi.de/entity/Q6534301"


@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_p4_symbols(mock_fetch):
    """P4 symbols (DLMF style) appear in profile.symbol with represents and optional xmlId."""
    entity = _formula_entity_p1460({
        "P4": [
            {
                "mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q1371"}}},
                "qualifiers": {
                    "P14": [{"datavalue": {"type": "string", "value": "x"}}],
                    "P5":  [{"datavalue": {"type": "string", "value": "C1.S4.E4.m2adec"}}],
                },
            }
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990006")
    symbols = resp.json()["profile"]["symbol"]
    assert len(symbols) == 1
    assert symbols[0]["represents"]["@id"] == "https://portal.mardi4nfdi.de/entity/Q1371"
    assert symbols[0]["notation"] == "x"
    assert symbols[0]["xmlId"] == "C1.S4.E4.m2adec"


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_single_identifier(mock_fetch):
    entity = _formula_entity_p1460({
        "P2": [{"mainsnak": {"datavalue": {"type": "string", "value": "1.5.E1"}}}],
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990007")
    identifier = resp.json()["profile"]["identifier"]
    assert isinstance(identifier, dict)
    assert identifier["propertyID"] == "dlmf"
    assert identifier["value"] == "1.5.E1"


@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_two_identifiers(mock_fetch):
    entity = _formula_entity_p1460({
        "P2":  [{"mainsnak": {"datavalue": {"type": "string", "value": "1.5.E1"}}}],
        "P12": [{"mainsnak": {"datavalue": {"type": "string", "value": "Q167920"}}}],
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990008")
    identifiers = resp.json()["profile"]["identifier"]
    assert isinstance(identifiers, list)
    assert len(identifiers) == 2
    prop_ids = {i["propertyID"] for i in identifiers}
    assert prop_ids == {"dlmf", "wikidata"}


# ---------------------------------------------------------------------------
# Optional fields
# ---------------------------------------------------------------------------

@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_named_after(mock_fetch):
    entity = _formula_entity_p1460({
        "P558": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q8896"}}}}],
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990009")
    named_after = resp.json()["profile"]["namedAfter"]
    assert named_after[0]["@id"] == "https://portal.mardi4nfdi.de/entity/Q8896"


@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_has_part_with_role(mock_fetch):
    entity = _formula_entity_p1460({
        "P1560": [
            {
                "mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q563"}}},
                "qualifiers": {
                    "P560": [{"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q9999"}}}]
                },
            }
        ]
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990010")
    parts = resp.json()["profile"]["hasPart"]
    assert len(parts) == 1
    assert parts[0]["@id"] == "https://portal.mardi4nfdi.de/entity/Q563"
    assert parts[0]["role"]["@id"] == "https://portal.mardi4nfdi.de/entity/Q9999"


@patch("app.mardi_fdo_server.fetch_entity")
def test_formula_same_as(mock_fetch):
    entity = _formula_entity_p1460({
        "P1690": [{"mainsnak": {"datavalue": {"type": "string", "value": "https://dlmf.nist.gov/5.2.E1"}}}],
    })
    mock_fetch.return_value = entity

    resp = client.get("/fdo/Q9990011")
    same_as = resp.json()["profile"]["sameAs"]
    assert "https://dlmf.nist.gov/5.2.E1" in same_as


# ---------------------------------------------------------------------------
# Type FDO endpoint
# ---------------------------------------------------------------------------

def test_formula_type_fdo_endpoint():
    resp = client.get("/fdo/types/Formula")
    assert resp.status_code == 200

    data = resp.json()
    assert data["@type"] == "DigitalObjectType"
    assert "mathExpression" in data["propertyMappings"]
    assert data["propertyMappings"]["mathExpression"]["pid"] == "P989"
