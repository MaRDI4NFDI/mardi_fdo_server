# Docker Setup for MaRDI FDO Server

This directory contains Docker configuration files to run the MaRDI FDO Server in a containerized environment.

## Quick Start

### Using Docker Compose (Recommended)

1. Build and run the container:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

2. The server will be available at `http://localhost:8000`

3. To run in detached mode:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d --build
   ```

4. To stop the container:
   ```bash
   docker-compose -f docker/docker-compose.yml down
   ```

### Using Docker directly

1. Build the image:
   ```bash
   docker build -f docker/Dockerfile -t mardi-fdo-server .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 mardi-fdo-server
   ```

## Development

The docker-compose setup mounts the source code as volumes, so changes to the code will be reflected immediately thanks to uvicorn's reload functionality.

## Testing

To run tests inside the container:
```bash
docker-compose -f docker/docker-compose.yml exec mardi-fdo-server pytest
```