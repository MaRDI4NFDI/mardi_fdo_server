"""Profile builder for mathematical formula items."""

from typing import Any, Dict, List, Optional

from app.fdo_config import ENTITY_IRI, FDO_IRI
from app.mardi_item_helper import (
    extract_item_ids,
    extract_string_claim,
    extract_string_claims,
    schema_refs_from_ids,
)


def _extract_p983_symbols(claims: Dict[str, Any]) -> List[Dict]:
    """P983 (in defining formula): math string main value, P984 qualifier for what it represents."""
    symbols = []
    for stmt in claims.get("P983", []):
        notation = stmt.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not isinstance(notation, str):
            continue
        entry: Dict[str, Any] = {"notation": notation}
        qualifiers = stmt.get("qualifiers", {})
        for q_val in qualifiers.get("P984", []):
            dv = q_val.get("datavalue", {})
            if dv.get("type") == "wikibase-entityid":
                entry["represents"] = {"@id": ENTITY_IRI + dv["value"]["id"]}
                break
        if "represents" not in entry:
            for q_val in qualifiers.get("P1962", []):
                dv = q_val.get("datavalue", {})
                if isinstance(dv.get("value"), str):
                    entry["represents"] = dv["value"]
                    break
        symbols.append(entry)
    return symbols


def _extract_p4_symbols(claims: Dict[str, Any]) -> List[Dict]:
    """P4 (symbols used, DLMF style): item main value, P14 qualifier for notation, P5 for xml-id."""
    symbols = []
    for stmt in claims.get("P4", []):
        dv = stmt.get("mainsnak", {}).get("datavalue", {})
        if dv.get("type") != "wikibase-entityid":
            continue
        represents_id = dv["value"].get("id")
        qualifiers = stmt.get("qualifiers", {})
        notation: Optional[str] = None
        xml_id: Optional[str] = None
        for q_val in qualifiers.get("P14", []):
            notation = q_val.get("datavalue", {}).get("value")
            break
        for q_val in qualifiers.get("P5", []):
            xml_id = q_val.get("datavalue", {}).get("value")
            break
        entry: Dict[str, Any] = {"represents": {"@id": ENTITY_IRI + represents_id}}
        if notation:
            entry["notation"] = notation
        if xml_id:
            entry["xmlId"] = xml_id
        symbols.append(entry)
    return symbols


def _extract_p1560_parts(claims: Dict[str, Any]) -> List[Dict]:
    """P1560 (contains): item parts with optional P560 role qualifier."""
    parts = []
    for stmt in claims.get("P1560", []):
        dv = stmt.get("mainsnak", {}).get("datavalue", {})
        if dv.get("type") != "wikibase-entityid":
            continue
        entry: Dict[str, Any] = {"@id": ENTITY_IRI + dv["value"]["id"]}
        for q_val in stmt.get("qualifiers", {}).get("P560", []):
            role_dv = q_val.get("datavalue", {})
            if role_dv.get("type") == "wikibase-entityid":
                entry["role"] = {"@id": ENTITY_IRI + role_dv["value"]["id"]}
                break
        parts.append(entry)
    return parts


def build_formula_profile(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    claims = entity.get("claims", {})
    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")

    # P989 (generic math string) preferred; fall back to P14 (DLMF contentmath)
    math_expression = extract_string_claim(claims, "P989") or extract_string_claim(claims, "P14")

    description_long = extract_string_claim(claims, "P1459")
    named_after_ids = extract_item_ids(claims, "P558")
    community_ids = extract_item_ids(claims, "P1495")
    related_urls = extract_string_claims(claims, "P1690")
    defines_symbol_ids = extract_item_ids(claims, "P3")
    dlmf_id = extract_string_claim(claims, "P2")
    wikidata_qid = extract_string_claim(claims, "P12")

    profile: Dict[str, Any] = {
        "@context": "https://schema.org/",
        "@type": "Formula",
        "@id": f"{FDO_IRI}{qid}",
        "name": label,
        "description": description,
        "url": f"{FDO_IRI}{qid}",
    }

    if math_expression:
        profile["mathExpression"] = math_expression

    if description_long:
        profile["description_long"] = description_long

    identifiers = []
    if dlmf_id:
        identifiers.append({
            "@type": "PropertyValue",
            "propertyID": "dlmf",
            "value": dlmf_id,
        })
    if wikidata_qid:
        identifiers.append({
            "@type": "PropertyValue",
            "propertyID": "wikidata",
            "value": wikidata_qid,
        })
    if len(identifiers) == 1:
        profile["identifier"] = identifiers[0]
    elif identifiers:
        profile["identifier"] = identifiers

    symbols = _extract_p983_symbols(claims) + _extract_p4_symbols(claims)
    if symbols:
        profile["symbol"] = symbols

    if defines_symbol_ids:
        profile["definesSymbol"] = schema_refs_from_ids(defines_symbol_ids)

    if named_after_ids:
        profile["namedAfter"] = schema_refs_from_ids(named_after_ids)

    if community_ids:
        profile["about"] = schema_refs_from_ids(community_ids)

    parts = _extract_p1560_parts(claims)
    if parts:
        profile["hasPart"] = parts

    if related_urls:
        profile["sameAs"] = related_urls

    return profile
