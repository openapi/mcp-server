FROM python:3.13-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

EXPOSE 8080

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "openapi_mcp_sdk.main"]
