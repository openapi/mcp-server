FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Espone la porta
EXPOSE 80

# Comando di avvio (modifica main:app se il file principale ha un nome diverso)
CMD ["python", "main.py"]