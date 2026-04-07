"""
Schema.org Dataset helpers for MaRDI FDO server.
"""
import mimetypes
from typing import Dict, Any, Tuple, Optional, List

from app.fdo_config import ENTITY_IRI, FDO_IRI
from app.mardi_item_helper import extract_time_claim, extract_string_claim, extract_item_ids, \
    schema_refs_from_ids, extract_qualifiers_for_item


def build_dataset_profile(qid: str, entity: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str], Dict[str, Any]]:
    """
    Construct a minimal schema.org Dataset profile from MediaWiki claims.

    No cross-entity expansion. No provenance modeling. Only direct claims
    mapped to schema.org.

    Args:
        qid: PID/QID string.
        entity: Raw entity dict from the KG, including labels and claims.

    Returns:
        Tuple containing:
        - Dict[str, Any]: schema:Dataset JSON-LD profile block.
        - Optional[str]: Download URL (P205) if present.
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
    community_ids = extract_item_ids(claims, "P1495") or []
    described_by_ids = extract_item_ids(claims, "P286") or []
    download_url = extract_string_claim(claims, "P205") or ""
    fileformat_ids = extract_item_ids(claims, "P204") or []
    openml_id = extract_string_claim(claims, "P1473") or ""

    # Get all items listed at "Components at storage" (P1827) to check
    # whether they belong to "fdo:hasComponent" or to "profile -> distribution"
    storage_item_ids = extract_item_ids(claims, "P1827") or []
    has_components_at_storage: Dict[str, Any] = {}
    storage_distributions: List[Dict[str, Any]] = []

    # Check for each item what type it is. If it is in:
    # "url" (P188), or "download link" (P504), or
    # "full work available at URL" (P205)
    # it will be added as a DataDownload in profile.distribution in the FDO JSON.
    # If not, it is unhandled here, but filtered in the calling method.
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

    # Identifiers: Zenodo (PropertyValue), DOI
    zenodo_id = extract_string_claim(claims, "P227") or ""
    doi_value = extract_string_claim(claims, "P27") or ""

    profile = {
        "@context": "https://schema.org/",
        "@type": "Dataset",
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

    if doi_value:
        profile["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "doi",
            "value": doi_value,
            "url": f"https://doi.org/{doi_value}"
        }
        profile.setdefault("sameAs", []).append(f"https://doi.org/{doi_value}")

    # Populate the "profile -> distributions" part
    distributions: List[Dict[str, Any]] = []
    if download_url:
        dist = {
            "@type": "DataDownload",
            "contentUrl": download_url,
        }
        if fileformat_ids:
            dist["encodingFormat"] = schema_refs_from_ids(fileformat_ids)[0]

        distributions.append(dist)

    distributions.extend(storage_distributions)

    unique_distributions: List[Dict[str, Any]] = []
    seen_distribution_urls = set()
    for distribution in distributions:
        content_url = distribution.get("contentUrl")
        if not content_url or content_url in seen_distribution_urls:
            continue
        seen_distribution_urls.add(content_url)
        unique_distributions.append(distribution)

    if unique_distributions:
        profile["distribution"] = unique_distributions

    if zenodo_id:
        profile.setdefault("sameAs", []).append(f"https://zenodo.org/record/{zenodo_id}")

    if openml_id:
        profile.setdefault("sameAs", []).append(
            f"https://www.openml.org/d/{openml_id}"
        )

    if community_ids:
        profile["about"] = schema_refs_from_ids(community_ids)

    if described_by_ids:
        profile["citation"] = schema_refs_from_ids(described_by_ids)

    return profile, download_url, has_components_at_storage
