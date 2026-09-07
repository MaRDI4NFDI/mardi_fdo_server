"""
Helper utilities for extracting structured data from MaRDI/Wikibase entities.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from app.fdo_config import (
    ENTITY_IRI,
    MAX_ENRICHED_REFS,
    QID_P1460_TYPE_MAP,
    QID_P31_TYPE_MAP,
    SCHEMA_TYPE_TO_TYPE_ID,
)


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


def extract_string_claims(claims: Dict[str, Any], prop: str) -> List[str]:
    """Return all string literals for the given property.

    Args:
        claims: MediaWiki claims block.
        prop: Property id whose literal values should be returned.

    Returns:
        List of all string literals (may be empty).
    """
    values: List[str] = []
    for statement in claims.get(prop, []):
        datavalue = statement.get("mainsnak", {}).get("datavalue")
        if datavalue and datavalue.get("type") == "string":
            val = datavalue.get("value")
            if val:
                values.append(val)
    return values


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


def schema_type_short(entity: Dict[str, Any]) -> Optional[str]:
    """Return the short schema type ID for an entity, from P31 or P1460.

    Args:
        entity: Raw entity dict from the KG, including claims.

    Returns:
        Short type ID such as ``Dataset``, or ``None`` if no mapping applies.
    """
    claims = entity.get("claims", {})
    for prop, qid_map in (("P31", QID_P31_TYPE_MAP), ("P1460", QID_P1460_TYPE_MAP)):
        for stmt in claims.get(prop, []):
            qid = stmt.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
            schema_type = qid_map.get(qid)
            if schema_type:
                return SCHEMA_TYPE_TO_TYPE_ID.get(schema_type)
    return None


def schema_refs_from_ids(
    ids: List[str],
    fetch_fn: Optional[Callable[[List[str]], Dict[str, Dict[str, Any]]]] = None,
    embed: Tuple[str, ...] = ("@type", "name"),
) -> List[Dict[str, str]]:
    """Return schema.org reference objects for a list of QIDs.

    Without ``fetch_fn`` each reference is a bare ``{"@id": ...}``. With it, the
    linked entities are resolved in one batched call and each reference also
    carries the fields named in ``embed`` - ``@type`` (from P31/P1460) and
    ``name`` (the English label).

    Resolution is best-effort: if the lookup fails, or an entity is missing, or
    no type mapping applies, the affected reference degrades to a bare ``@id``
    rather than raising. At most ``MAX_ENRICHED_REFS`` references are enriched.

    Args:
        ids: List of QIDs.
        fetch_fn: Optional batched lookup taking a list of QIDs and returning a
            ``{qid: entity}`` mapping.
        embed: Which extra fields to copy onto each reference.

    Returns:
        List of reference dictionaries, each with at least ``@id``.
    """
    refs: List[Dict[str, str]] = [{"@id": ENTITY_IRI + _id} for _id in ids]
    if fetch_fn is None or not ids or not embed:
        return refs

    to_resolve = list(dict.fromkeys(ids))[:MAX_ENRICHED_REFS]
    try:
        linked = fetch_fn(to_resolve) or {}
    except Exception:  # never let enrichment turn a good record into an error
        return refs

    for _id, ref in zip(ids, refs):
        entity = linked.get(_id)
        if not entity:
            continue
        if "@type" in embed:
            schema_type = schema_type_short(entity)
            if schema_type:
                ref["@type"] = schema_type
        if "name" in embed:
            name = entity.get("labels", {}).get("en", {}).get("value")
            if name:
                ref["name"] = name
    return refs


def embedded_fields(type_id: str, field: str) -> Tuple[str, ...]:
    """Return the extra fields to embed on references of ``field``.

    Reads the ``embed`` key of the field's propertyMappings entry in
    TYPE_REGISTRY, so the type FDO a client retrieves and the record it receives
    describe the same thing.

    Args:
        type_id: Short type ID, e.g. ``ScholarlyArticle``.
        field: Profile field name, e.g. ``citation``.

    Returns:
        Tuple of field names such as ``("@type", "name")``; empty if the field
        is not declared as enriched.
    """
    from app.type_registry import TYPE_REGISTRY

    mapping = TYPE_REGISTRY.get(type_id, {}).get("propertyMappings", {}).get(field, {})
    return tuple(mapping.get("embed", ()))


def refs_for_field(
    type_id: str,
    field: str,
    ids: List[str],
    fetch_fn: Optional[Callable[[List[str]], Dict[str, Dict[str, Any]]]] = None,
) -> List[Dict[str, str]]:
    """Return references for ``field``, enriched if its type declares ``embed``.

    Args:
        type_id: Short type ID of the record being built.
        field: Profile field name, e.g. ``citation``.
        ids: Linked QIDs.
        fetch_fn: Batched entity lookup.

    Returns:
        List of reference dictionaries.
    """
    embed = embedded_fields(type_id, field)
    if embed and fetch_fn is not None:
        return schema_refs_from_ids(ids, fetch_fn=fetch_fn, embed=embed)
    return schema_refs_from_ids(ids)


def normalize_created_modified(entity: Dict[str, Any]) -> Tuple[Optional[str], str]:
    created = entity.get("created") or None
    modified = entity.get("modified") or None
    if modified is None and created is not None:
        modified = created
    if modified is None:
        from datetime import datetime, timezone
        modified = datetime.now(timezone.utc).isoformat()
    return created, modified


def extract_qualifiers_for_item(claims: Dict[str, Any], prop: str, target_item_id: str) -> Dict[str, Any]:
    """Extract qualifiers from a specific property statement for a target item.

    Args:
        claims: MediaWiki claims block.
        prop: Property id (e.g., ``P1827``).
        target_item_id: Item ID to extract qualifiers for (e.g., ``Q6830870``).

    Returns:
        Dictionary of qualifier properties and their values.
    """
    qualifiers_dict: Dict[str, Any] = {}
    for statement in claims.get(prop, []):
        datavalue = statement.get("mainsnak", {}).get("datavalue")
        if datavalue and datavalue.get("type") == "wikibase-entityid":
            item_id = datavalue["value"].get("id")
            if item_id == target_item_id:
                qualifiers = statement.get("qualifiers", {})
                for qualifier_prop, qualifier_values in qualifiers.items():
                    for qual_value in qualifier_values:
                        q_datavalue = qual_value.get("datavalue")
                        if q_datavalue:
                            if q_datavalue.get("type") == "wikibase-entityid":
                                qualifiers_dict[qualifier_prop] = q_datavalue["value"].get("id")
                            elif q_datavalue.get("type") == "string":
                                qualifiers_dict[qualifier_prop] = q_datavalue.get("value")
                            elif q_datavalue.get("type") == "time":
                                time_val = q_datavalue.get("value", {}).get("time", "")
                                if time_val:
                                    time_val = time_val.lstrip("+")
                                    if time_val.endswith("T00:00:00Z"):
                                        time_val = time_val.replace("T00:00:00Z", "")
                                    qualifiers_dict[qualifier_prop] = time_val
                break
    return qualifiers_dict