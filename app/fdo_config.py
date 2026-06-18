"""
Configuration and static data structures for the MaRDI FDO Server.
"""

ENTITY_IRI = "https://portal.mardi4nfdi.de/entity/"
FDO_IRI = "https://fdo.portal.mardi4nfdi.de/fdo/"
FDO_ACCESS_IRI = "https://fdo.portal.mardi4nfdi.de/access/"
DOIP_IRI = "https://doip.portal.mardi4nfdi.de/doip/retrieve"

# Base URI for MaRDI-owned type FDOs. Append the type ID to get the resolvable URI,
# e.g. FDO_TYPE_BASE_URI + "ScholarlyArticle" → the type FDO served at /fdo/types/ScholarlyArticle.
FDO_TYPE_BASE_URI = f"{FDO_IRI}types/"

# Maps the internal schema: type strings (used by guess_type_from_claims) to the short
# type IDs that form the MaRDI-owned digitalObjectType URIs.
SCHEMA_TYPE_TO_TYPE_ID: dict = {
    "schema:ScholarlyArticle":    "ScholarlyArticle",
    "schema:Person":              "Person",
    "schema:Dataset":             "Dataset",
    "schema:Workflow":            "Workflow",
    "schema:SoftwareApplication": "SoftwareApplication",
    "schema:SoftwareSourceCode":  "SoftwareSourceCode",
}

# Maps Wikibase QIDs to internal/schema.org type strings, based on P31 ("instance of").
QID_P31_TYPE_MAP = {
    "Q56887": "schema:ScholarlyArticle",
    "Q57162": "schema:Person",
    "Q56885": "schema:Dataset",
    "Q57080": "schema:SoftwareSourceCode",
    "Q56605": "schema:SoftwareSourceCode",
    "Q68657": "schema:Workflow",
}

# Maps Wikibase QIDs to internal/schema.org type strings, based on P1460 ("MaRDI profile type").
QID_P1460_TYPE_MAP = {
    "Q5976450": "schema:SoftwareApplication",
    "Q5984635": "schema:Dataset",
    "Q6534216": "schema:Workflow",
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
