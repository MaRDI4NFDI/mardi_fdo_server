# MaRDI FastAPI FDO Prototype

Minimal FastAPI service that exposes FAIR Digital Object payloads for existing
MaRDI QIDs. It queries the current MediaWiki/Knowledge-Graph backend, wraps the
result into a lightweight JSON-LD structure, and serves it under `/fdo/{qid}`.

## Preparation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
uvicorn mardi_fdo_server:app --reload --port 8000
```

Request an entity: `curl http://localhost:8000/fdo/Q123456`.

## Deployment Notes

- Run the container/pod alongside the existing MaRDI stack
- Expose it - e.g. via Traefik 
- The service is read-only - it only queries the MediaWiki/SPARQL backends
