"""

Schema.org Person helpers for MaRDI FDO prototype.
"""

from typing import Any, Dict, List, Optional
from app.mardi_item_helper import (
    BASE_IRI,
    extract_item_ids,
    extract_string_claim,
    schema_refs_from_ids,
)



def build_author_payload(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:

    """Construct schema.org Person JSON-LD from a Wikibase entity."""
    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    claims = entity.get("claims", {})


    # Note: Property IDs here are provisional and should be verified against the MaRDI Wikibase

    affiliation_ids = extract_item_ids(claims, "P1416")  # Affiliation
    website = extract_string_claim(claims, "P856")       # Official website
    orcid = extract_string_claim(claims, "P496")         # ORCID iD

    author: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": BASE_IRI + qid,
        "name": label,
        "description": description,
        "url": BASE_IRI + qid,
    }

    if affiliation_ids:
        author["affiliation"] = schema_refs_from_ids(affiliation_ids)

    if website:
        author["sameAs"] = [website]
        
    if orcid:

        # Add ORCID to identifiers if present
        author.setdefault("identifier", [])

        if isinstance(author["identifier"], dict):
             author["identifier"] = [author["identifier"]]
        
        author["identifier"].append({
            "@type": "PropertyValue",
            "propertyID": "orcid",
            "value": orcid,
            "url": f"https://orcid.org/{orcid}"
        })

    return author

