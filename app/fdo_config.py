"""
Configuration and static data structures for the MaRDI FDO Server.
"""

# Maps Wikibase QIDs to internal/schema.org type strings.
QID_TYPE_MAP = {
    "Q56887": "schema:ScholarlyArticle",
    "Q57162": "schema:Person",
}

# JSON-LD Context definition for FDO payloads.
JSONLD_CONTEXT = [
    "https://w3id.org/fdo/context/v1",
    {
        "schema": "https://schema.org/",
        "prov": "http://www.w3.org/ns/prov#",
        "fdo": "https://w3id.org/fdo/vocabulary/",
        "kernel": "fdo:kernel",
        "access": "fdo:access",
        "accessURL": "fdo:accessURL",
        "mediaType": "fdo:mediaType",
    },
]
