"""
Minimal FastAPI service exposing FAIR Digital Objects (FDOs) for MaRDI QIDs.
"""
import re
from functools import lru_cache
from typing import Any, Dict

import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.mardi_item_helper import normalize_created_modified, extract_item_ids
from fdo_schemas.dataset import build_dataset_profile
from fdo_schemas.publication import build_scholarly_article_profile
from fdo_schemas.person import build_author_payload
from app.fdo_config import QID_TYPE_MAP, JSONLD_CONTEXT, FDO_IRI, FDO_ACCESS_IRI, ENTITY_IRI

MW_API = "https://portal.mardi4nfdi.de/w/api.php"
KERNEL_VERSION = "v1"

app = FastAPI(
    title="MaRDI FDO façade",
    description="Lightweight FastAPI service returning minimal FDO payloads for MaRDI QIDs.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@lru_cache(maxsize=2048)
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
        return QID_TYPE_MAP.get(instance_qid, instance_qid or "mardi:UnknownType")
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
    profile, pdf_url = build_scholarly_article_profile(qid, entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": "https://schema.org/ScholarlyArticle",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    components = []
    if pdf_url:
        components.append({
            "@id": f"#fulltext",
            "componentId": f"fulltext",
            "mediaType": "application/pdf"
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
        "digitalObjectType": "https://schema.org/Person",
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
    profile, download_url = build_dataset_profile(qid, entity)

    created, modified = normalize_created_modified(entity)

    kernel = {
        "@id": fdo_id,
        "digitalObjectType": "https://schema.org/Dataset",
        "primaryIdentifier": f"mardi:{qid}",
        "kernelVersion": KERNEL_VERSION,
        "immutable": True,
        "modified": modified,
    }
    if created:
        kernel["created"] = created

    # Only add if payload / download url exists
    components = []
    if download_url:
        components.append({
            "@id": "#rocrate",
            "componentId": "rocrate",
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


@app.get("/fdo/{object_id}")
def get_fdo(object_id: str):
    qid = object_id.upper()

    _QID_PATTERN = re.compile(r"^Q[0-9]+(?:_FULLTEXT)?$", re.IGNORECASE)
    if not _QID_PATTERN.match(qid):
        raise HTTPException(status_code=400, detail="invalid FDO identifier")

    try:
        entity = fetch_entity(qid)
    except Exception as exc:
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
