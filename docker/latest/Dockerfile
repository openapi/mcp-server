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
EXPOSE 8080

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "openapi_mcp_sdk.main"]