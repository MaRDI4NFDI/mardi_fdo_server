"""
Helper utilities for extracting structured data from MaRDI/Wikibase entities.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.fdo_config import ENTITY_IRI


def extract_item_ids(claims: Dict[str, Any], prop: str) -> List[str]:
    """Extract referenced entity IDs for a given property.

    Args:
        claims: MediaWiki claims block.
        prop: Property id (e.g., ``P50`` for author).

    Returns:
        List of QIDs referenced by the property.
    """
    ids: List[str] = []
    for statement in claims.get(prop, []):
        datavalue = statement.get("mainsnak", {}).get("datavalue")
        if datavalue and datavalue.get("type") == "wikibase-entityid":
            ids.append(datavalue["value"].get("id"))
    return ids


def extract_string_claim(claims: Dict[str, Any], prop: str) -> Optional[str]:
    """Return the first string literal for the given property.

    Args:
        claims: MediaWiki claims block.
        prop: Property id whose literal value should be returned.

    Returns:
        First string literal or ``None`` if absent.
    """
    statements = claims.get(prop)
    if not statements:
        return None
    datavalue = statements[0].get("mainsnak", {}).get("datavalue")
    if not datavalue:
        return None
    return datavalue.get("value")


def extract_time_claim(claims: Dict[str, Any], prop: str) -> Optional[str]:
    """Return ISO date string from a Wikibase time value.

    Args:
        claims: MediaWiki claims block.
        prop: Property id that stores a time value (e.g., ``P577``).

    Returns:
        ISO date string or ``None`` if not available.
    """
    statements = claims.get(prop)
    if not statements:
        return None
    datavalue = statements[0].get("mainsnak", {}).get("datavalue", {})
    value = datavalue.get("value", {})
    time_val = value.get("time")
    if not time_val:
        return None
    time_val = time_val.lstrip("+")
    if time_val.endswith("T00:00:00Z"):
        time_val = time_val.replace("T00:00:00Z", "")
    return time_val


def schema_refs_from_ids(ids: List[str]) -> List[Dict[str, str]]:
    """Return schema.org reference objects for a list of QIDs.

    Args:
        ids: List of QIDs.

    Returns:
        List of dictionaries with ``@id`` references.
    """
    return [{"@id": ENTITY_IRI + _id} for _id in ids]


def normalize_created_modified(entity: Dict[str, Any]) -> Tuple[Optional[str], str]:
    created = entity.get("created") or None
    modified = entity.get("modified") or None
    if modified is None and created is not None:
        modified = created
    if modified is None:
        from datetime import datetime, timezone
        modified = datetime.now(timezone.utc).isoformat()
    return created, modified