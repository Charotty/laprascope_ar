# Docker & Docker-Compose Deployment

This document describes how to run the **backend API** (FastAPI) together with an **Orthanc DICOM server** using Docker.

## Folder Structure
```
./docker/
  ├─ backend/
  │   └─ Dockerfile
  ├─ orthanc/
  │   └─ orthanc.json
  └─ docker-compose.yml
```

## backend/Dockerfile
```Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## orthanc/orthanc.json (minimal config)
```json
{
  "Name" : "LaprascopeOrthanc",
  "StorageDirectory" : "/var/lib/orthanc/db",
  "HttpServerEnabled" : true,
  "HttpPort" : 8042,
  "RemoteAccessAllowed" : true
}
```

## docker-compose.yml
```yaml
version: "3.9"
services:
  api:
    build: ./docker/backend
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - orthanc

  orthanc:
    image: jodogne/orthanc
    volumes:
      - orthanc-db:/var/lib/orthanc/db
      - ./docker/orthanc/orthanc.json:/etc/orthanc/orthanc.json:ro
    ports:
      - "8042:8042"
volumes:
  orthanc-db:
```

## Usage
```bash
# Build containers
docker compose build
# Start stack
docker compose up -d

# API available at http://localhost:8000/docs
# Orthanc UI at http://localhost:8042
```

### Development Hot-Reload
Add the following override:
```yaml
services:
  api:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
```

---

## Future Improvements
* Use Celery + Redis containers for background jobs.
* Automate image push in CI.
