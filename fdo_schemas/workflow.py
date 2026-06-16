"""
Schema.org Workflow helpers for MaRDI FDO server.
"""
import mimetypes
from typing import Dict, Any, Tuple, List

from app.fdo_config import FDO_IRI
from app.mardi_item_helper import extract_time_claim, extract_string_claim, extract_item_ids, \
    schema_refs_from_ids, extract_qualifiers_for_item, extract_monolingualtext_claim


def build_workflow_profile(qid: str, entity: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Construct a minimal schema.org Workflow profile from MediaWiki claims.

    Args:
        qid: PID/QID string.
        entity: Raw entity dict from the KG, including labels and claims.

    Returns:
        Tuple containing:
        - Dict[str, Any]: schema:Workflow JSON-LD profile block.
        - Dict[str, Any]: Components at storage qualifier information (P1827).
    """
    claims = entity.get("claims", {})

    # Authors
    author_ids = extract_item_ids(claims, "P16")

    # Properties
    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    publication_date = extract_time_claim(claims, "P28") or ""
    license_ids = extract_item_ids(claims, "P163")
    described_by_ids = extract_item_ids(claims, "P286") or []
    storage_item_ids = extract_item_ids(claims, "P1827") or []

    zenodo_id = extract_string_claim(claims, "P227") or ""
    problem_statement = extract_string_claim(claims, "P1604") or ""
    summary = extract_monolingualtext_claim(claims, "P1638") or ""

    profile = {
        "@context": "https://schema.org/",
        "@type": "Workflow",
        "@id": f"{FDO_IRI}{qid}",
        "name": label,
        "description": description,
        "url": f"{FDO_IRI}{qid}",
    }

    if publication_date:
        profile["datePublished"] = publication_date

    if author_ids:
        profile["creator"] = schema_refs_from_ids(author_ids)

    if license_ids:
        profile["license"] = schema_refs_from_ids(license_ids)

    # Distributions come exclusively from "stored at" (P1827) qualifier URLs.
    has_components_at_storage: Dict[str, Any] = {}
    storage_distributions: List[Dict[str, Any]] = []

    for item_id in storage_item_ids:
        qualifiers = extract_qualifiers_for_item(claims, "P1827", item_id)
        has_components_at_storage[item_id] = qualifiers
        for qualifier_prop in ("P188", "P205", "P504"):
            storage_url = qualifiers.get(qualifier_prop)
            if not isinstance(storage_url, str) or not storage_url:
                continue
            storage_distribution: Dict[str, Any] = {
                "@type": "DataDownload",
                "contentUrl": storage_url,
            }
            guessed_media_type, _ = mimetypes.guess_type(storage_url)
            if guessed_media_type:
                storage_distribution["encodingFormat"] = guessed_media_type
            storage_distributions.append(storage_distribution)

    # Deduplicate distributions by contentUrl.
    unique_distributions: List[Dict[str, Any]] = []
    seen_distribution_urls = set()
    for distribution in storage_distributions:
        content_url = distribution.get("contentUrl")
        if not content_url or content_url in seen_distribution_urls:
            continue
        seen_distribution_urls.add(content_url)
        unique_distributions.append(distribution)

    if unique_distributions:
        profile["distribution"] = unique_distributions

    if zenodo_id:
        profile.setdefault("sameAs", []).append(f"https://zenodo.org/record/{zenodo_id}")

    if problem_statement:
        profile["problem_statement"] = problem_statement

    if summary:
        profile["summary"] = summary

    if described_by_ids:
        profile["citation"] = schema_refs_from_ids(described_by_ids)

    return profile, has_components_at_storage
