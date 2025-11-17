"""
Schema.org ScholarlyArticle helpers for MaRDI FDO prototype.
"""

from typing import Any, Dict, List, Optional

from app.mardi_item_helper import (
    BASE_IRI,
    extract_item_ids,
    extract_string_claim,
    extract_time_claim,
    schema_refs_from_ids,
)


def build_scholarly_article_payload(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """Construct schema.org ScholarlyArticle JSON-LD from a Wikibase entity."""
    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    claims = entity.get("claims", {})

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

    page_start: Optional[str] = None
    page_end: Optional[str] = None
    if page_range and "-" in page_range:
        parts = page_range.split("-", maxsplit=1)
        page_start, page_end = parts[0], parts[1]

    article: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": BASE_IRI + qid,
        "name": label,
        "headline": label,
        "description": description,
        "url": BASE_IRI + qid,
        "datePublished": publication_date,
    }
    if author_ids:
        article["author"] = schema_refs_from_ids(author_ids)
    if container_ids:
        article["isPartOf"] = schema_refs_from_ids(container_ids)
    if publisher_ids:
        article["publisher"] = schema_refs_from_ids(publisher_ids)
    if subject_ids:
        article["about"] = schema_refs_from_ids(subject_ids)
    if language_ids:
        article["inLanguage"] = [BASE_IRI + lang for lang in language_ids]
    if doi_value:
        article["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "doi",
            "value": doi_value,
            "url": f"https://doi.org/{doi_value}",
        }
        article["sameAs"] = [f"https://doi.org/{doi_value}"]
    if page_start:
        article["pageStart"] = page_start
    if page_end:
        article["pageEnd"] = page_end
    if page_range:
        article["pagination"] = page_range
    if license_ids:
        article["license"] = schema_refs_from_ids(license_ids)
    if comment:
        article["comment"] = comment
    if keyword_ids:
        article["keyword"] = schema_refs_from_ids(keyword_ids)
    if citation_ids:
        article["citation"] = schema_refs_from_ids(citation_ids)
    return article
