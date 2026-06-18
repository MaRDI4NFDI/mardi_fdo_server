"""
Schema.org ScholarlyArticle helpers for MaRDI FDO server.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.fdo_config import ENTITY_IRI
from app.mardi_item_helper import (
    extract_item_ids,
    extract_qualifiers_for_item,
    extract_string_claim,
    extract_string_claims,
    extract_time_claim,
    schema_refs_from_ids,
)


def build_scholarly_article_profile(qid: str, entity: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str], Dict[str, Any]]:
    claims = entity.get("claims", {})

    arxiv_id = extract_string_claim(claims, "P21")
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    author_ids = extract_item_ids(claims, "P16")
    author_name = extract_string_claim(claims, "P43")
    citation_ids = extract_item_ids(claims, "P223")
    recommended_ids = extract_item_ids(claims, "P1643")
    container_ids = extract_item_ids(claims, "P1433")
    msc_codes = extract_string_claims(claims, "P226")
    publisher_ids = extract_item_ids(claims, "P200")
    license_ids = extract_item_ids(claims, "P275")
    language_ids = extract_item_ids(claims, "P407")
    keywords = extract_string_claims(claims, "P1450")
    zbmath_de_number = extract_string_claim(claims, "P1451")
    zbmath_open_id = extract_string_claim(claims, "P225")
    publication_date = extract_time_claim(claims, "P28") or ""
    doi_value = extract_string_claim(claims, "P27") or ""
    page_range = extract_string_claim(claims, "P304")
    comment = extract_string_claim(claims, "P1448")

    page_start, page_end = None, None
    if page_range and "-" in page_range:
        page_start, page_end = page_range.split("-", maxsplit=1)

    profile = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": f"{ENTITY_IRI}{qid}",
        "name": label,
        "headline": label,
        "description": description,
        "url": f"{ENTITY_IRI}{qid}",
        "datePublished": publication_date
    }

    if author_ids:
        profile["author"] = schema_refs_from_ids(author_ids)
    if author_name:
        profile["authorName"] = author_name
    if container_ids:
        profile["isPartOf"] = schema_refs_from_ids(container_ids)
    if publisher_ids:
        profile["publisher"] = schema_refs_from_ids(publisher_ids)
    if msc_codes:
        profile["about"] = msc_codes
    if language_ids:
        profile["inLanguage"] = [f"{ENTITY_IRI}{lid}" for lid in language_ids]

    identifiers = []
    if doi_value:
        identifiers.append({"@type": "PropertyValue", "propertyID": "doi", "value": doi_value, "url": f"https://doi.org/{doi_value}"})
        profile["sameAs"] = [f"https://doi.org/{doi_value}"]
    if zbmath_de_number:
        identifiers.append({"@type": "PropertyValue", "propertyID": "zbmath-de", "value": zbmath_de_number, "url": f"https://zbmath.org/?q=an:{zbmath_de_number}"})
    if zbmath_open_id:
        identifiers.append({"@type": "PropertyValue", "propertyID": "zbmath-open", "value": zbmath_open_id})
    if identifiers:
        profile["identifier"] = identifiers[0] if len(identifiers) == 1 else identifiers

    if page_start:
        profile["pageStart"] = page_start
    if page_end:
        profile["pageEnd"] = page_end
    if page_range:
        profile["pagination"] = page_range
    if license_ids:
        profile["license"] = schema_refs_from_ids(license_ids)
    if comment:
        profile["comment"] = comment
    if keywords:
        profile["keywords"] = keywords
    if citation_ids:
        profile["citation"] = schema_refs_from_ids(citation_ids)
    if recommended_ids:
        profile["relatedLink"] = schema_refs_from_ids(recommended_ids)

    storage_item_ids = extract_item_ids(claims, "P1827") or []
    has_components_at_storage: Dict[str, Any] = {}
    for item_id in storage_item_ids:
        has_components_at_storage[item_id] = extract_qualifiers_for_item(claims, "P1827", item_id)

    return profile, pdf_url, has_components_at_storage

