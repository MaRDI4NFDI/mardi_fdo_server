"""
Schema.org ScholarlyArticle helpers for MaRDI FDO server.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.fdo_config import ENTITY_IRI
from app.mardi_item_helper import (
    extract_item_ids,
    extract_string_claim,
    extract_time_claim,
    schema_refs_from_ids,
)


def build_scholarly_article_profile(qid: str, entity: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    claims = entity.get("claims", {})

    arxiv_id = extract_string_claim(claims, "P21")
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    author_ids = extract_item_ids(claims, "P16")
    citation_ids = extract_item_ids(claims, "P223")
    container_ids = extract_item_ids(claims, "P1433")
    subject_ids = extract_item_ids(claims, "P226")
    publisher_ids = extract_item_ids(claims, "P200")
    license_ids = extract_item_ids(claims, "P275")
    language_ids = extract_item_ids(claims, "P407")
    keyword_ids = extract_item_ids(claims, "1450")
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
    if container_ids:
        profile["isPartOf"] = schema_refs_from_ids(container_ids)
    if publisher_ids:
        profile["publisher"] = schema_refs_from_ids(publisher_ids)
    if subject_ids:
        profile["about"] = schema_refs_from_ids(subject_ids)
    if language_ids:
        profile["inLanguage"] = [f"{ENTITY_IRI}{lid}" for lid in language_ids]

    if doi_value:
        profile["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "doi",
            "value": doi_value,
            "url": f"https://doi.org/{doi_value}"
        }
        profile["sameAs"] = [f"https://doi.org/{doi_value}"]

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
    if keyword_ids:
        profile["keyword"] = schema_refs_from_ids(keyword_ids)
    if citation_ids:
        profile["citation"] = schema_refs_from_ids(citation_ids)

    return profile, pdf_url

