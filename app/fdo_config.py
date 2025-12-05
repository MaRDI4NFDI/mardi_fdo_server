"""
Configuration and static data structures for the MaRDI FDO Server.
"""

ENTITY_IRI = "https://portal.mardi4nfdi.de/entity/"
FDO_IRI = "https://fdo.portal.mardi4nfdi.de/fdo/"
FDO_ACCESS_IRI = "https://fdo.portal.mardi4nfdi.de/access/"

# Maps Wikibase QIDs to internal/schema.org type strings, based on P31 ("instance of").
QID_P31_TYPE_MAP = {
    "Q56887": "schema:ScholarlyArticle",
    "Q57162": "schema:Person",
    "Q56885": "schema:Dataset",
    "Q57080": "schema:SoftwareSourceCode",
}

# Maps Wikibase QIDs to internal/schema.org type strings, based on P1460 ("MaRDI profiel type").
QID_P1460_TYPE_MAP = {
    "Q5976450": "schema:SoftwareApplication",
    "Q5984635": "schema:Dataset",
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
