FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY app.py .

# Exposer le port Streamlit
EXPOSE 8501

# Variable d'environnement pour Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_PORT=8501

# Commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]