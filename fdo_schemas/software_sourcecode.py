"""
Schema.org SoftwareSourceCode helpers for MaRDI FDO server.
"""

from typing import Any, Dict, Optional, Tuple

from app.fdo_config import FDO_IRI
from app.mardi_item_helper import (
    extract_item_ids,
    extract_string_claim,
    extract_time_claim,
    schema_refs_from_ids,
)


def build_software_sourcecode_profile(qid: str, entity: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
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

    profile: Dict[str, Any] = {
        "@context": "https://schema.org/",
        "@type": "SoftwareSourceCode",
        "@id": f"{FDO_IRI}{qid}",
        "name": label,
        "description": description,
        "url": f"{FDO_IRI}{qid}",
    }

    if author_ids:
        profile["creator"] = schema_refs_from_ids(author_ids)

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
        profile["citation"] = schema_refs_from_ids(described_by_ids)

    return profile, download_url, documentation_pdf_url
