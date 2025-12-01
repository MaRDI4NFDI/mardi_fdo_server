"""
Schema.org Dataset helpers for MaRDI FDO server.
"""
from typing import Dict, Any, Tuple, Optional

from app.fdo_config import ENTITY_IRI, FDO_IRI
from app.mardi_item_helper import extract_time_claim, extract_string_claim, extract_item_ids, \
    schema_refs_from_ids


def build_dataset_profile(qid: str, entity: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Construct a minimal schema.org Dataset profile from MediaWiki claims.

    No cross-entity expansion. No provenance modeling. Only direct claims
    mapped to schema.org.

    Args:
        qid: PID/QID string.
        entity: Raw entity dict from the KG, including labels and claims.

    Returns:
        Dict[str, Any]: schema:Dataset JSON-LD profile block.
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

    if download_url:
        dist = {
            "@type": "DataDownload",
            "contentUrl": download_url,
        }
        if fileformat_ids:
            dist["encodingFormat"] = schema_refs_from_ids(fileformat_ids)[0]

        profile["distribution"] = [dist]

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

    return profile, download_url