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
            "author":        {"pid": "P16",   "type": "item",   "multi": True},
            "datePublished": {"pid": "P28",   "type": "time",   "multi": False},
            "identifier":    {"pid": "P27",   "type": "string", "multi": False, "note": "DOI"},
            "license":       {"pid": "P275",  "type": "item",   "multi": True},
            "inLanguage":    {"pid": "P407",  "type": "item",   "multi": True},
            "isPartOf":      {"pid": "P1433", "type": "item",   "multi": True,  "note": "container publication"},
            "pageStart":     {"pid": "P304",  "type": "string", "multi": False, "note": "page range string, e.g. '12-34'"},
            "publisher":     {"pid": "P200",  "type": "item",   "multi": True},
            "about":         {"pid": "P226",  "type": "item",   "multi": True},
            "citation":      {"pid": "P223",  "type": "item",   "multi": True},
            "comment":       {"pid": "P1448", "type": "string", "multi": False},
            "arxivId":       {"pid": "P21",   "type": "string", "multi": False},
        },
    },
    "Dataset": {
        "label": "Dataset",
        "description": "A dataset in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/Dataset",
        "propertyMappings": {
            "creator":        {"pid": "P16",   "type": "item",   "multi": True},
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
            "creator":           {"pid": "P16",   "type": "item",   "multi": True},
            "datePublished":     {"pid": "P28",   "type": "time",   "multi": False},
            "license":           {"pid": "P163",  "type": "item",   "multi": True},
            "citation":          {"pid": "P286",  "type": "item",   "multi": True,  "note": "described by"},
            "zenodoId":          {"pid": "P227",  "type": "string", "multi": False},
            "problem_statement": {"pid": "P1604", "type": "string",           "multi": False},
            "summary":           {"pid": "P1638", "type": "monolingualtext", "multi": False},
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
            "creator":             {"pid": "P16",   "type": "item",   "multi": True},
            "license":             {"pid": "P163",  "type": "item",   "multi": True},
            "operatingSystem":     {"pid": "P306",  "type": "item",   "multi": True},
            "citation":            {"pid": "P286",  "type": "item",   "multi": True},
            "datePublished":       {"pid": "P28",   "type": "time",   "multi": False},
            "softwareVersion":     {"pid": "P132",  "type": "string", "multi": False},
            "programmingLanguage": {"pid": "P114",  "type": "string", "multi": False},
            "codeRepository":      {"pid": "P339",  "type": "url",    "multi": False},
            "distribution":        {"pid": "P205",  "type": "url",    "multi": False, "note": "download URL"},
            "identifier":          {"pid": "P27",   "type": "string", "multi": False, "note": "DOI"},
            "softwareHeritageId":  {"pid": "P1454", "type": "string", "multi": False},
        },
    },
    "SoftwareSourceCode": {
        "label": "Software Source Code",
        "description": "Software source code in the MaRDI knowledge graph.",
        "seeAlso": "https://schema.org/SoftwareSourceCode",
        "propertyMappings": {
            "creator":             {"pid": "P16",   "type": "item",   "multi": True},
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
}
