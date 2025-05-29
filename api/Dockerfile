FROM python:3.9-slim

WORKDIR /app

# Copier et installer les dépendances
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

# Copier le code source
COPY main.py .

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]