FROM python:3.13-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# TODO: Remove legacy dependency — port 80 is the Google Cloud Run default. Standard Docker
# convention is 8080. Change EXPOSE and the CMD port when decoupled from Cloud Run,
# and align with the PORT env var default in main.py.
EXPOSE 80

# TODO: Remove legacy dependency — this CMD uses pip + requirements.txt which includes
# GCP-specific packages. Switch to `uv` and pyproject.toml (already present) to get a
# reproducible, platform-agnostic build: CMD ["uv", "run", "uvicorn", "openapi_mcp_server.main:app"]
CMD ["python", "-m", "src.openapi_mcp_server.main"]