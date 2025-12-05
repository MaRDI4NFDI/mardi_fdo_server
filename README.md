# MaRDI FastAPI FDO Prototype

Minimal FastAPI service that exposes FAIR Digital Object payloads for existing
MaRDI QIDs. It queries the current MediaWiki/Knowledge-Graph backend, wraps the
result into a lightweight JSON-LD structure, and serves it under `/fdo/{qid}`.

## Preparation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m venv .venv
.\venv\Scripts\activate.ps1
pip install -r requirements.txt
```

## Run the server

### Standalone server

```bash
uvicorn app.mardi_fdo_server:app --reload --port 8000 
```

### Docker

The project can be run using Docker for easy deployment and development.

1. Build the image:
   ```bash
   docker build -f docker/Dockerfile -t mardi-fdo-server .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 mardi-fdo-server
   ```


## Request an entity
   ```bash
   curl http://localhost:8000/fdo/Q123456
   ```


## Deployment Notes

- Run the container/pod alongside the existing MaRDI stack
- Expose it - e.g. via Traefik 
- The service is read-only - it only queries the MediaWiki/SPARQL backends
