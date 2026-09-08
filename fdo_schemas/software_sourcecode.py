"""
Schema.org SoftwareSourceCode helpers for MaRDI FDO server.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from app.fdo_config import FDO_IRI, PROFILE_CONTEXT
from app.mardi_item_helper import (
    extract_item_ids,
    extract_qualifiers_for_item,
    extract_string_claim,
    extract_time_claim,
    schema_refs_from_ids, refs_for_field,
)


def build_software_sourcecode_profile(
    qid: str,
    entity: Dict[str, Any],
    fetch_fn: Optional[Callable[[List[str]], Dict[str, Dict[str, Any]]]] = None,
) -> Tuple[Dict[str, Any], Optional[str], Optional[str], Dict[str, Any]]:
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
    described_by_ids = extract_item_ids(claims, "P286")
    publication_date = extract_time_claim(claims, "P28") or ""
    software_version = extract_string_claim(claims, "P132") or ""
    programming_language = extract_item_ids(claims, "P114") or ""
    software_heritage_id = extract_string_claim(claims, "P1454") or ""
    repository_url = extract_string_claim(claims, "P339") or ""
    download_url = extract_string_claim(claims, "P205") or ""
    doi_value = extract_string_claim(claims, "P27") or ""

    cran_name = extract_string_claim(claims, "P229") or ""
    documentation_pdf_url = f"https://cran.r-project.org/web/packages/{cran_name}/{cran_name}.pdf" if cran_name else None

    # P1459 "Description (long)" has no schema.org equivalent, so it is emitted
    # under the MaRDI namespace rather than forced into description or abstract.
    description_long = extract_string_claim(claims, "P1459") or ""

    profile: Dict[str, Any] = {
        "@context": PROFILE_CONTEXT,
        "@type": "SoftwareSourceCode",
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

    if publication_date:
        profile["datePublished"] = publication_date

    if software_version:
        profile["softwareVersion"] = software_version

    if programming_language:
        profile["programmingLanguage"] = programming_language

    if repository_url:
        profile["codeRepository"] = repository_url

    if download_url:
        distribution = {
            "@type": "DataDownload",
            "contentUrl": download_url,
        }
        profile["distribution"] = [distribution]

    if doi_value:
        doi_url = f"https://doi.org/{doi_value}"
        profile["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "doi",
            "value": doi_value,
            "url": doi_url,
        }
        profile.setdefault("sameAs", []).append(doi_url)

    if described_by_ids:
        profile["citation"] = refs_for_field("SoftwareSourceCode", "citation", described_by_ids, fetch_fn)

    storage_item_ids = extract_item_ids(claims, "P1827") or []
    has_components_at_storage: Dict[str, Any] = {}
    for item_id in storage_item_ids:
        has_components_at_storage[item_id] = extract_qualifiers_for_item(claims, "P1827", item_id)

    return profile, download_url, documentation_pdf_url, has_components_at_storage
