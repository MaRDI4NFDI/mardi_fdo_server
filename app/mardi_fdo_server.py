"""
Minimal FastAPI service exposing FAIR Digital Objects (FDOs) for MaRDI QIDs.
"""
import logging
import mimetypes
import re

_log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
_handler = logging.StreamHandler()
_handler.setFormatter(_log_formatter)

for _name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    _logger = logging.getLogger(_name)
    _logger.handlers = [_handler]
    _logger.propagate = False

logger = logging.getLogger(__name__)
logger.handlers = [_handler]
logger.propagate = False
from typing import Any, Dict

import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.mardi_item_helper import normalize_created_modified, extract_item_ids
from fdo_schemas.dataset import build_dataset_profile
from fdo_schemas.workflow import build_workflow_profile
from fdo_schemas.software_application import build_software_application_profile
from fdo_schemas.software_sourcecode import build_software_sourcecode_profile
from fdo_schemas.publication import build_scholarly_article_profile
from fdo_schemas.person import build_author_payload
from app.fdo_config import QID_P31_TYPE_MAP, JSONLD_CONTEXT, FDO_IRI, FDO_ACCESS_IRI, ENTITY_IRI, \
    QID_P1460_TYPE_MAP, DOIP_IRI, FDO_TYPE_BASE_URI
from app.type_registry import TYPE_REGISTRY

MW_API = "https://portal.mardi4nfdi.de/w/api.php"
KERNEL_VERSION = "v1"

app = FastAPI(
    title="MaRDI FDO façade",
    description="Lightweight FastAPI service returning minimal FDO payloads for MaRDI QIDs.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


def fetch_entity(qid: str) -> Dict[str, Any]:
    """Look up a QID via the MediaWiki API.

    Args:
        qid: Identifier such as ``Q123``.

    Returns:
        Parsed entity JSON returned by the MediaWiki service.

    Raises:
        HTTPException: If the QID does not exist in the backend.
    """
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": qid,
        "props": "labels|descriptions|claims|info",
        "languages": "en",
    }
    resp = httpx.get(MW_API, params=params, timeout=5)
    resp.raise_for_status()
    entities = resp.json().get("entities", {})
    if qid not in entities:
        raise HTTPException(status_code=404, detail=f"QID {qid} not found")
    return entities[qid]


def guess_type_from_claims(claims: Dict[str, Any]) -> str:
    """Infer an approximate type for the entity from P31.

    Args:
        claims: MediaWiki claims block.

    Returns:
        Identifier representing the entity type.
    """
    instance_stmt = claims.get("P31", [])
    if instance_stmt:
        mainsnak = instance_stmt[0].get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})
        instance_qid = value.get("id", "")
        return QID_P31_TYPE_MAP.get(instance_qid, instance_qid or "mardi:UnknownType")

    # If P31 ("instance of") is not set, try P1460 ("MaRDI profile type")

    instance_stmt = claims.get("P1460", [])
    if instance_stmt:
        mainsnak = instance_stmt[0].get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})
        instance_qid = value.get("id", "")
        return QID_P1460_TYPE_MAP.get(instance_qid, instance_qid or "mardi:UnknownType")

    return "mardi:UnknownType"


def to_fdo(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """Route to publication or generic FDO transformers based on type.

    Args:
        qid: Identifier of the entity.
        entity: Raw entity JSON.

    Returns:
        ``FDOResponse`` tailored to the entity type.
    """
    claims = entity.get("claims", {})
    entity_type = guess_type_from_claims(claims)
    
    # Local dispatcher mapping types to handler functions
    # Defined here or at module level to map strings to functions
    handler = TYPE_HANDLER_MAP.get(entity_type, to_fdo_minimal)
    return handler(qid, entity)


def to_fdo_publication(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    fdo_id = f"{FDO_IRI}{qid}"
    created, modified = normalize_created_modified(entity)
    profile, pdf_url, has_components_at_storage = build_scholarly_article_profile(qid, entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": f"{FDO_TYPE_BASE_URI}ScholarlyArticle",
        "seeAlso": "https://schema.org/ScholarlyArticle",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    components = []
    existing_component_ids: set = set()
    for qualifiers in has_components_at_storage.values():
        if "P1828" not in qualifiers:
            continue
        filename = qualifiers.get("P1828")
        if not filename or filename in existing_component_ids:
            continue
        guessed_media_type, _ = mimetypes.guess_type(filename)
        components.append({
            "@id": f"#{filename}",
            "componentId": filename,
            "mediaType": guessed_media_type or "application/octet-stream",
        })
        existing_component_ids.add(filename)
    if pdf_url and not existing_component_ids:
        components.append({
            "@id": "#fulltext.pdf",
            "componentId": "fulltext.pdf",
            "mediaType": "application/pdf",
        })
    if components:
        kernel["fdo:hasComponent"] = components

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/"
            }
        ],
        "@id": fdo_id,
        "@type": "DigitalObject",
        "kernel": kernel,
        "profile": profile,
        "provenance": {
            "prov:generatedAtTime": modified,
            "prov:wasAttributedTo": "MaRDI Knowledge Graph"
        }
    }



def to_fdo_person(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    fdo_id = f"{FDO_IRI}{qid}"
    created, modified = normalize_created_modified(entity)
    profile = build_author_payload(qid, entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": f"{FDO_TYPE_BASE_URI}Person",
        "seeAlso": "https://schema.org/Person",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created is not None:
        kernel["created"] = created

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/"
            }
        ],
        "@id": fdo_id,
        "@type": "schema:Person",
        "kernel": kernel,
        "profile": profile,
        "provenance": {
            "prov:generatedAtTime": modified,
            "prov:wasAttributedTo": "MaRDI Knowledge Graph",
        },
    }


def to_fdo_dataset(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an FDO-compliant JSON-LD representation for a dataset object.

    Produces a Digital Object record where the `digitalObjectType` is a
    schema.org Dataset. The resulting kernel declares a single component
    with componentId `"rocrate"`, pointing to a dynamically retrievable
    RO-Crate ZIP representation of the dataset. The object's PID (QID) is
    assigned as the primaryIdentifier. A minimal profile block is included
    using schema.org Dataset fields derived from the input entity.

    Args:
        qid: PID/QID string identifying the dataset in the MaRDI Knowledge Graph.
        entity: Metadata extracted from the KG for the dataset (label, timestamps).

    Returns:
        Dict[str, Any]: Complete FDO JSON-LD payload including:
            - DigitalObject envelope with context definitions
            - Kernel section with dataset type and component reference to RO-Crate
            - Profile section describing the dataset content
            - Provenance markers for timestamp and attribution

    Raises:
        KeyError: If required fields are missing from the `entity`.
    """
    fdo_id = f"{FDO_IRI}{qid}"
    profile, download_url, has_components_at_storage = build_dataset_profile(qid, entity)

    created, modified = normalize_created_modified(entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": f"{FDO_TYPE_BASE_URI}Dataset",
        "seeAlso": "https://schema.org/Dataset",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    # Keep a RO-Crate component when a direct dataset download URL is present.
    components = []
    if download_url:
        components.append({
            "@id": "#rocrate.zip",
            "componentId": "rocrate.zip",
            "mediaType": "application/zip",
        })

    # Handle entries from the "stored at" (P1827) section of the item
    # Only keep entries that have the qualifier "FDO component id" (P1828)
    existing_component_ids = {component["componentId"] for component in components}
    for qualifiers in has_components_at_storage.values():
        if "P1828" not in qualifiers:
            continue
        filename = qualifiers.get("P1828")
        if not filename or filename in existing_component_ids:
            continue
        guessed_media_type, _ = mimetypes.guess_type(filename)
        components.append({
            "@id": f"#{filename}",
            "componentId": filename,
            "mediaType": guessed_media_type or "application/octet-stream",
        })
        existing_component_ids.add(filename)
    
    if components:
        kernel["fdo:hasComponent"] = components

    # Add additional entries to "profile -> distribution" for all file-like components
    # in "fdo:hasComponent" (except the virtual "#rocrate.zip" entry)
    distribution_entries = profile.get("distribution", [])
    if not isinstance(distribution_entries, list):
        distribution_entries = []

    # Keep track of existing distribution URLs to avoid duplicates.
    seen_distribution_urls = {
        entry.get("contentUrl")
        for entry in distribution_entries
        if isinstance(entry, dict) and entry.get("contentUrl")
    }

    # Create one DataDownload distribution entry per component (except rocrate.zip).
    for component in components:
        component_id = component.get("componentId")
        if not component_id or component.get("@id") == "#rocrate.zip":
            continue
        retrieve_url = f"{DOIP_IRI}/{qid}/{component_id}"
        if retrieve_url in seen_distribution_urls:
            continue

        distribution_entry = {
            "@type": "DataDownload",
            "contentUrl": retrieve_url,
        }
        media_type = component.get("mediaType")
        if media_type:
            distribution_entry["encodingFormat"] = media_type

        distribution_entries.append(distribution_entry)
        seen_distribution_urls.add(retrieve_url)

    # Write back all collected distribution entries.
    if distribution_entries:
        profile["distribution"] = distribution_entries

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/"
            }
        ],
        "@id": fdo_id,
        "@type": "DigitalObject",
        "kernel": kernel,
        "profile": profile,
        "provenance": {
            "prov:generatedAtTime": modified,
            "prov:wasAttributedTo": "MaRDI Knowledge Graph"
        }
    }


def to_fdo_workflow(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an FDO-compliant JSON-LD representation for a workflow object.

    Args:
        qid: PID/QID string identifying the workflow in the MaRDI Knowledge Graph.
        entity: Metadata extracted from the KG for the workflow (label, timestamps).

    Returns:
        Dict[str, Any]: Complete FDO JSON-LD payload including:
            - DigitalObject envelope with context definitions
            - Kernel section with workflow type and component references
            - Profile section describing the workflow content
            - Provenance markers for timestamp and attribution
    """
    fdo_id = f"{FDO_IRI}{qid}"
    profile, has_components_at_storage = build_workflow_profile(qid, entity, fetch_fn=fetch_entity)

    created, modified = normalize_created_modified(entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": f"{FDO_TYPE_BASE_URI}Workflow",
        "seeAlso": "https://schema.org/Workflow",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    # Components come only from P1827 entries that carry a P1828 qualifier.
    components = []
    existing_component_ids: set = set()
    for qualifiers in has_components_at_storage.values():
        if "P1828" not in qualifiers:
            continue
        filename = qualifiers.get("P1828")
        if not filename or filename in existing_component_ids:
            continue
        guessed_media_type, _ = mimetypes.guess_type(filename)
        components.append({
            "@id": f"#{filename}",
            "componentId": filename,
            "mediaType": guessed_media_type or "application/octet-stream",
        })
        existing_component_ids.add(filename)

    if components:
        kernel["fdo:hasComponent"] = components

    # Enrich profile -> distribution with one DataDownload per component.
    distribution_entries = profile.get("distribution", [])
    if not isinstance(distribution_entries, list):
        distribution_entries = []

    seen_distribution_urls = {
        entry.get("contentUrl")
        for entry in distribution_entries
        if isinstance(entry, dict) and entry.get("contentUrl")
    }

    for component in components:
        component_id = component.get("componentId")
        if not component_id:
            continue
        retrieve_url = f"{DOIP_IRI}/{qid}/{component_id}"
        if retrieve_url in seen_distribution_urls:
            continue
        distribution_entry = {
            "@type": "DataDownload",
            "contentUrl": retrieve_url,
        }
        media_type = component.get("mediaType")
        if media_type:
            distribution_entry["encodingFormat"] = media_type
        distribution_entries.append(distribution_entry)
        seen_distribution_urls.add(retrieve_url)

    if distribution_entries:
        profile["distribution"] = distribution_entries

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/"
            }
        ],
        "@id": fdo_id,
        "@type": "DigitalObject",
        "kernel": kernel,
        "profile": profile,
        "provenance": {
            "prov:generatedAtTime": modified,
            "prov:wasAttributedTo": "MaRDI Knowledge Graph"
        }
    }


def to_fdo_software_application(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """Build an FDO JSON-LD payload for software application entities.

    Args:
        qid: PID/QID string that identifies the software application in the MaRDI KG.
        entity: MediaWiki entity payload containing labels, descriptions, and claims.

    Returns:
        Dict[str, Any]: Digital Object with kernel, profile, and provenance sections.

    Raises:
        KeyError: If mandatory fields are missing from ``entity``.
    """
    fdo_id = f"{FDO_IRI}{qid}"
    profile, download_url, has_components_at_storage = build_software_application_profile(qid, entity)

    created, modified = normalize_created_modified(entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": f"{FDO_TYPE_BASE_URI}SoftwareApplication",
        "seeAlso": "https://schema.org/SoftwareApplication",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    components = []
    existing_component_ids: set = set()
    for qualifiers in has_components_at_storage.values():
        if "P1828" not in qualifiers:
            continue
        filename = qualifiers.get("P1828")
        if not filename or filename in existing_component_ids:
            continue
        guessed_media_type, _ = mimetypes.guess_type(filename)
        components.append({
            "@id": f"#{filename}",
            "componentId": filename,
            "mediaType": guessed_media_type or "application/octet-stream",
        })
        existing_component_ids.add(filename)
    if download_url and not existing_component_ids:
        components.append({
            "@id": "#software-archive",
            "componentId": "software-archive",
            "mediaType": "application/zip",
        })
    if components:
        kernel["fdo:hasComponent"] = components

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/"
            }
        ],
        "@id": fdo_id,
        "@type": "DigitalObject",
        "kernel": kernel,
        "profile": profile,
        "provenance": {
            "prov:generatedAtTime": modified,
            "prov:wasAttributedTo": "MaRDI Knowledge Graph"
        }
    }


def to_fdo_software_sourcecode(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """Build an FDO JSON-LD payload for software source code entities.

    Args:
        qid: PID/QID string that identifies the software source code in the MaRDI KG.
        entity: MediaWiki entity payload containing labels, descriptions, and claims.

    Returns:
        Dict[str, Any]: Digital Object with kernel, profile, and provenance sections.

    Raises:
        KeyError: If mandatory fields are missing from ``entity``.
    """
    fdo_id = f"{FDO_IRI}{qid}"
    profile, download_url, documentation_pdf_url, has_components_at_storage = build_software_sourcecode_profile(qid, entity)

    created, modified = normalize_created_modified(entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": f"{FDO_TYPE_BASE_URI}SoftwareSourceCode",
        "seeAlso": "https://schema.org/SoftwareSourceCode",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    components = []
    existing_component_ids: set = set()
    for qualifiers in has_components_at_storage.values():
        if "P1828" not in qualifiers:
            continue
        filename = qualifiers.get("P1828")
        if not filename or filename in existing_component_ids:
            continue
        guessed_media_type, _ = mimetypes.guess_type(filename)
        components.append({
            "@id": f"#{filename}",
            "componentId": filename,
            "mediaType": guessed_media_type or "application/octet-stream",
        })
        existing_component_ids.add(filename)
    if not existing_component_ids:
        if download_url:
            components.append({
                "@id": "#software-archive",
                "componentId": "software-archive",
                "mediaType": "application/zip",
            })
        if documentation_pdf_url:
            components.append({
                "@id": "#documentation.pdf",
                "componentId": "documentation.pdf",
                "mediaType": "application/pdf",
            })
    if components:
        kernel["fdo:hasComponent"] = components

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/"
            }
        ],
        "@id": fdo_id,
        "@type": "DigitalObject",
        "kernel": kernel,
        "profile": profile,
        "provenance": {
            "prov:generatedAtTime": modified,
            "prov:wasAttributedTo": "MaRDI Knowledge Graph"
        }
    }


def to_fdo_minimal(qid: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """Transform an arbitrary entity into a minimal FDO payload.

    Args:
        qid: Identifier of the entity.
        entity: Raw entity JSON.

    Returns:
        ``FDOResponse`` containing kernel/access/provenance blocks.
    """
    label = entity.get("labels", {}).get("en", {}).get("value", qid)
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    entity_type = guess_type_from_claims(entity.get("claims", {}))
    return {
        "@context": JSONLD_CONTEXT,
        "@id": ENTITY_IRI + qid,
        "@type": entity_type,
        "kernel": {
            "@type": entity_type,
            "name": label,
            "description": description,
        },
        "access": {
            "accessURL": f"{ENTITY_IRI}{qid}",
            "mediaType": "application/vnd.mardi.entity+json",
        },
        "prov:generatedAtTime": entity.get("modified", ""),
        "prov:wasAttributedTo": "MaRDI Knowledge Graph",
    }

# Local dispatcher mapping types to handler functions
TYPE_HANDLER_MAP = {
    "schema:ScholarlyArticle": to_fdo_publication,
    "schema:Person": to_fdo_person,
    "schema:Dataset": to_fdo_dataset,
    "schema:Workflow": to_fdo_workflow,
    "schema:SoftwareApplication": to_fdo_software_application,
    "schema:SoftwareSourceCode": to_fdo_software_sourcecode,
}


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Render a greeting with a usage hint on the landing page.

    Returns:
        HTMLResponse: Greeting and sample FDO link with styled background.
    """
    body = """
    <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            color: #0b132b;
            background: url('/static/background_mardi_api.png') no-repeat center center fixed;
            background-size: cover;
          }
          .overlay {
            background-color: rgba(255, 255, 255, 0.85);
            max-width: 720px;
            margin: 12vh auto;
            padding: 32px 36px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
          }
          a {
            color: #1a73e8;
            text-decoration: none;
            font-weight: 600;
          }
          a:hover {
            text-decoration: underline;
          }
        </style>
      </head>
      <body>
        <div class="overlay">
          <p>Hello, this is the MaRDI FDO service.</p>
          <p>
            This API delivers FAIR Digital Object payloads for MaRDI QIDs.
            Try <a href="/fdo/Q2055155">/fdo/Q2055155</a>.
          </p>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=body)


@app.get("/fdo/types/{type_id}")
def get_fdo_type(type_id: str):
    """Return the type FDO for a MaRDI-owned digital object type.

    The returned document contains ``propertyMappings``, a machine-readable
    table mapping Schema.org field names to Wikibase P-IDs. Clients use this
    to translate field names into the P-ID keys expected by the UPDATE handler.
    """
    if type_id not in TYPE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Type '{type_id}' not found in MaRDI type registry")

    entry = TYPE_REGISTRY[type_id]
    type_uri = f"{FDO_TYPE_BASE_URI}{type_id}"

    return {
        "@context": [
            "https://w3id.org/fdo/context/v1",
            {
                "schema": "https://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "fdo": "https://w3id.org/fdo/vocabulary/",
            },
        ],
        "@id": type_uri,
        "@type": "DigitalObjectType",
        "kernel": {
            "@id": type_uri,
            "digitalObjectType": f"{FDO_TYPE_BASE_URI}FDOType",
            "primaryIdentifier": f"mardi:types/{type_id}",
            "kernelVersion": KERNEL_VERSION,
            "immutable": True,
        },
        "label": entry["label"],
        "description": entry["description"],
        "seeAlso": entry["seeAlso"],
        "propertyMappings": entry["propertyMappings"],
    }


@app.get("/fdo/{object_id}")
def get_fdo(object_id: str):
    qid = object_id.upper()

    _QID_PATTERN = re.compile(r"^Q[0-9]+(?:_FULLTEXT)?$", re.IGNORECASE)
    if not _QID_PATTERN.match(qid):
        raise HTTPException(status_code=400, detail="invalid FDO identifier")

    try:
        entity = fetch_entity(qid)
    except httpx.ReadTimeout:
        logger.error("Timeout fetching %s from MW API (timeout=5s)", qid)
        raise HTTPException(status_code=504, detail=f"Upstream timeout fetching {qid}")
    except httpx.HTTPStatusError as exc:
        logger.error("MW API returned %s for %s", exc.response.status_code, qid)
        raise HTTPException(status_code=502, detail=f"Upstream error for {qid}: {exc.response.status_code}")
    except Exception as exc:
        logger.exception("Unexpected error fetching %s: %s", qid, exc)
        raise

    return to_fdo(qid, entity)


@app.get("/health")
async def health() -> Dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Return empty favicon response to silence 404s."""
    return Response(content=b"", media_type="image/x-icon", status_code=204)


@app.get("/robots.txt", include_in_schema=False)
async def robots() -> Response:
    """Return a permissive robots.txt to silence 404s."""
    return Response(content="User-agent: *\nDisallow: /\n", media_type="text/plain")
