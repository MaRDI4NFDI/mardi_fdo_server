"""
Static registry of MaRDI FDO type definitions with Schema.org → Wikibase property mappings.

propertyMappings encodes how Schema.org field names (as they appear in the profile block of
item FDOs) correspond to Wikibase property IDs (P-numbers) in the MaRDI knowledge graph.

A DOIP client constructing an UPDATE payload should:
  1. RETRIEVE the item FDO and read kernel.digitalObjectType.
  2. RETRIEVE that type FDO (e.g. RETRIEVE fdo/types/ScholarlyArticle).
  3. Consult propertyMappings to translate Schema.org field names to P-IDs.
  4. Send an UPDATE with {"properties": {"P28": "2024", "P16": "Q123", ...}}.

Mapping fields:
  pid   — Wikibase property ID (e.g. "P28")
  type  — value kind: "item" (QID reference), "string", "time" (ISO 8601), "url"
  multi — whether multiple values are accepted
  note  — optional clarification (not machine-readable)
"""

from typing import Any, Dict

TYPE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ScholarlyArticle": {
        "label": "Scholarly Article",
        "description": "A peer-reviewed academic publication in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/ScholarlyArticle",
        "propertyMappings": {
            "author":               {"pid": "P16",   "type": "item",   "multi": True},
            "authorName":           {"pid": "P43",   "type": "string", "multi": False},
            "datePublished":        {"pid": "P28",   "type": "time",   "multi": False},
            "identifier":           {"pid": "P27",   "type": "string", "multi": False, "note": "DOI"},
            "license":              {"pid": "P275",  "type": "item",   "multi": True},
            "inLanguage":           {"pid": "P407",  "type": "item",   "multi": True},
            "isPartOf":             {"pid": "P1433", "type": "item",   "multi": True,  "note": "container publication (journal/proceedings)"},
            "pageStart":            {"pid": "P304",  "type": "string", "multi": False, "note": "page range string, e.g. '12-34'"},
            "publisher":            {"pid": "P200",  "type": "item",   "multi": True},
            "about":                {"pid": "P226",  "type": "string", "multi": True,  "note": "MSC codes, e.g. '65H17'"},
            "keywords":             {"pid": "P1450", "type": "string", "multi": True,  "note": "zbMATH keywords"},
            "identifier/zbmath-de": {"pid": "P1451", "type": "string", "multi": False, "note": "zbMATH DE number"},
            "identifier/zbmath-open": {"pid": "P225", "type": "string", "multi": False, "note": "zbMATH Open document ID"},
            "relatedLink":          {"pid": "P1643", "type": "item",   "multi": True,  "note": "recommended / related articles"},
            "hasPart":              {"pid": "P1560", "type": "item",   "multi": True,  "note": "formulas contained in this publication"},
            "citation":             {"pid": "P223",  "type": "item",   "multi": True},
            "comment":              {"pid": "P1448", "type": "string", "multi": False},
            "arxivId":              {"pid": "P21",   "type": "string", "multi": False},
            "arXivClassification":  {"pid": "P22",   "type": "string", "multi": False, "note": "arXiv subject classification, e.g. 'math.OC'"},
        },
    },
    "Dataset": {
        "label": "Dataset",
        "description": "A dataset in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/Dataset",
        "propertyMappings": {
            "author":         {"pid": "P16",   "type": "item",   "multi": True},
            "authorName":     {"pid": "P43",   "type": "string", "multi": False},
            "datePublished":  {"pid": "P28",   "type": "time",   "multi": False},
            "license":        {"pid": "P163",  "type": "item",   "multi": True},
            "identifier":     {"pid": "P27",   "type": "string", "multi": False, "note": "DOI"},
            "distribution":   {"pid": "P205",  "type": "url",    "multi": False, "note": "download URL"},
            "encodingFormat": {"pid": "P204",  "type": "item",   "multi": True},
            "about":          {"pid": "P1495", "type": "item",   "multi": True,  "note": "communities"},
            "citation":       {"pid": "P286",  "type": "item",   "multi": True,  "note": "described by"},
            "zenodoId":       {"pid": "P227",  "type": "string", "multi": False},
            "openMlId":       {"pid": "P1473", "type": "string", "multi": False},
        },
    },
    "Workflow": {
        "label": "Workflow",
        "description": "A computational workflow in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/Workflow",
        "propertyMappings": {
            "author":            {"pid": "P16",   "type": "item",   "multi": True},
            "authorName":        {"pid": "P43",   "type": "string", "multi": False},
            "datePublished":     {"pid": "P28",   "type": "time",   "multi": False},
            "license":           {"pid": "P163",  "type": "item",   "multi": True},
            "citation":          {"pid": "P286",  "type": "item",   "multi": True,  "note": "described by"},
            "uses":              {"pid": "P557",  "type": "item",   "multi": True,  "note": "dataset or resource used by this workflow"},
            "zenodoId":          {"pid": "P227",  "type": "string", "multi": False},
            "description_long":  {"pid": "P1459", "type": "string", "multi": False},
        },
    },
    "Person": {
        "label": "Person",
        "description": "A researcher or contributor in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/Person",
        "propertyMappings": {
            "affiliation": {"pid": "P17", "type": "item",   "multi": True},
            "url":         {"pid": "P29", "type": "url",    "multi": False},
            "identifier":  {"pid": "P20", "type": "string", "multi": False, "note": "ORCID"},
        },
    },
    "SoftwareApplication": {
        "label": "Software Application",
        "description": "A software application in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/SoftwareApplication",
        "propertyMappings": {
            "author":                           {"pid": "P16",   "type": "item",   "multi": True},
            "authorName":                       {"pid": "P43",   "type": "string", "multi": False},
            "license":                          {"pid": "P163",  "type": "item",   "multi": True},
            "operatingSystem":                  {"pid": "P306",  "type": "item",   "multi": True},
            "citation":                         {"pid": "P286",  "type": "item",   "multi": True},
            "similarSoftware":                  {"pid": "P1458", "type": "item",   "multi": True},
            "datePublished":                    {"pid": "P28",   "type": "time",   "multi": False},
            "softwareVersion":                  {"pid": "P132",  "type": "string", "multi": False},
            "programmingLanguage":              {"pid": "P114",  "type": "string", "multi": False},
            "codeRepository":                   {"pid": "P339",  "type": "url",    "multi": False},
            "sameAs":                           {"pid": "P29",   "type": "url",    "multi": False, "note": "official website"},
            "distribution":                     {"pid": "P205",  "type": "url",    "multi": False, "note": "download URL"},
            "identifier":                       {"pid": "P27",   "type": "string", "multi": False, "note": "DOI"},
            "softwareHeritageId":               {"pid": "P1454", "type": "string", "multi": False},
            "additionalProperty/swMATH":        {"pid": "P13",   "type": "string", "multi": False, "note": "swMATH work ID"},
            "mathematicsSubjectClassification": {"pid": "P226",  "type": "string", "multi": True},
        },
    },
    "SoftwareSourceCode": {
        "label": "Software Source Code",
        "description": "Software source code in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/SoftwareSourceCode",
        "propertyMappings": {
            "author":              {"pid": "P16",   "type": "item",   "multi": True},
            "authorName":          {"pid": "P43",   "type": "string", "multi": False},
            "license":             {"pid": "P163",  "type": "item",   "multi": True},
            "citation":            {"pid": "P286",  "type": "item",   "multi": True},
            "datePublished":       {"pid": "P28",   "type": "time",   "multi": False},
            "softwareVersion":     {"pid": "P132",  "type": "string", "multi": False},
            "programmingLanguage": {"pid": "P114",  "type": "item",   "multi": True},
            "codeRepository":      {"pid": "P339",  "type": "url",    "multi": False},
            "distribution":        {"pid": "P205",  "type": "url",    "multi": False, "note": "download URL"},
            "identifier":          {"pid": "P27",   "type": "string", "multi": False, "note": "DOI"},
            "softwareHeritageId":  {"pid": "P1454", "type": "string", "multi": False},
            "cranName":            {"pid": "P229",  "type": "string", "multi": False},
        },
    },
    "Formula": {
        "label": "Formula",
        "description": "A mathematical formula in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/Formula",
        "propertyMappings": {
            "mathExpression":          {"pid": "P989",  "type": "string", "multi": False, "note": "defining formula (math string); P14 used as fallback for DLMF-sourced items"},
            "description_long":        {"pid": "P1459", "type": "string", "multi": False},
            "symbol":                  {"pid": "P983",  "type": "string", "multi": True,  "note": "symbol notation (math string); qualifier P984 for the concept it represents"},
            "definesSymbol":           {"pid": "P3",    "type": "item",   "multi": True},
            "identifier/dlmf":         {"pid": "P2",    "type": "string", "multi": False, "note": "DLMF equation ID"},
            "identifier/wikidata":     {"pid": "P12",   "type": "string", "multi": False, "note": "Wikidata QID"},
            "namedAfter":              {"pid": "P558",  "type": "item",   "multi": True},
            "about":                   {"pid": "P1495", "type": "item",   "multi": True,  "note": "mathematical community or subject area"},
            "hasPart":                 {"pid": "P1560", "type": "item",   "multi": True,  "note": "contained sub-formulas; qualifier P560 for the role"},
            "sameAs":                  {"pid": "P1690", "type": "url",    "multi": True,  "note": "related external resource"},
        },
    },
}
