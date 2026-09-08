"""
Schema.org SoftwareSourceCode helpers for MaRDI FDO server.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from app.fdo_config import FDO_IRI, PROFILE_CONTEXT
from app.mardi_item_helper import (
    extract_item_ids,
    extract_qualifiers_for_item,
    extract_string_claim,
    extract_string_claims,
    extract_time_claim,
    schema_refs_from_ids, refs_for_field,
)


def build_software_application_profile(
    qid: str,
    entity: Dict[str, Any],
    fetch_fn: Optional[Callable[[List[str]], Dict[str, Dict[str, Any]]]] = None,
) -> Tuple[Dict[str, Any], Optional[str], Dict[str, Any]]:
    """Construct a minimal schema.org SoftwareSourceCode profile.

    Args:
        qid: PID/QID string identifying the software record.
        entity: Raw entity data from the MaRDI Knowledge Graph.

    Returns:
        Tuple[Dict[str, Any], Optional[str]]: A schema.org profile block and an optional
        download URL for the software archive.
    """
    claims = entity.get("claims", {})

    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")

    author_ids = extract_item_ids(claims, "P16")
    author_name = extract_string_claim(claims, "P43")
    license_ids = extract_item_ids(claims, "P163")
    operating_system_ids = extract_item_ids(claims, "P306") # TODO: Find correct pid
    described_by_ids = extract_item_ids(claims, "P286")
    similar_software_ids = extract_item_ids(claims, "P1458")
    publication_date = extract_time_claim(claims, "P28") or ""
    software_version = extract_string_claim(claims, "P132") or ""
    programming_language = extract_string_claim(claims, "P114") or ""
    software_heritage_id = extract_string_claim(claims, "P1454") or ""
    repository_url = extract_string_claim(claims, "P339") or ""
    official_website = extract_string_claim(claims, "P29") or ""
    download_url = extract_string_claim(claims, "P205") or ""
    doi_value = extract_string_claim(claims, "P27") or ""
    swmath_id = extract_string_claim(claims, "P13") or ""
    msc_codes = extract_string_claims(claims, "P226")

    # P1459 "Description (long)" has no schema.org equivalent, so it is emitted
    # under the MaRDI namespace rather than forced into description or abstract.
    description_long = extract_string_claim(claims, "P1459") or ""

    profile: Dict[str, Any] = {
        "@context": PROFILE_CONTEXT,
        "@type": "SoftwareApplication",
        "@id": f"{FDO_IRI}{qid}",
        "name": label,
        "description": description,
        "url": f"{FDO_IRI}{qid}",
    }
    if description_long:
        profile["mardi:descriptionLong"] = description_long

    if author_ids:
        profile["author"] = schema_refs_from_ids(author_ids)

    if author_name:
        profile["authorName"] = author_name

    if license_ids:
        profile["license"] = schema_refs_from_ids(license_ids)

    if operating_system_ids:
        profile["operatingSystem"] = schema_refs_from_ids(operating_system_ids)

    if publication_date:
        profile["datePublished"] = publication_date

    if software_version:
        profile["softwareVersion"] = software_version

    if repository_url:
        profile["codeRepository"] = repository_url

    if download_url:
        distribution = {
            "@type": "DataDownload",
            "contentUrl": download_url,
        }
        profile["distribution"] = [distribution]

    if official_website and official_website != repository_url:
        profile.setdefault("sameAs", []).append(official_website)

    if doi_value:
        doi_url = f"https://doi.org/{doi_value}"
        profile["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "doi",
            "value": doi_value,
            "url": doi_url,
        }
        profile.setdefault("sameAs", []).append(doi_url)

    if swmath_id:
        profile.setdefault("additionalProperty", []).append({
            "@type": "PropertyValue",
            "propertyID": "swMATH",
            "value": swmath_id,
            "url": f"https://swmath.org/software/{swmath_id}",
        })

    if software_heritage_id:
        profile["softwareHeritageId"] = software_heritage_id

    if msc_codes:
        profile["mathematicsSubjectClassification"] = msc_codes

    if described_by_ids:
        profile["citation"] = refs_for_field("SoftwareApplication", "citation", described_by_ids, fetch_fn)

    if similar_software_ids:
        profile["similarSoftware"] = schema_refs_from_ids(similar_software_ids)

    storage_item_ids = extract_item_ids(claims, "P1827") or []
    has_components_at_storage: Dict[str, Any] = {}
    for item_id in storage_item_ids:
        has_components_at_storage[item_id] = extract_qualifiers_for_item(claims, "P1827", item_id)

    return profile, download_url, has_components_at_storage
