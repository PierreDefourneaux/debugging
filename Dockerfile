FROM python:3.10-slim

WORKDIR /app

COPY app/requirements.txt .


RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copier le reste du projet en excluant les dossiers cachés et l'environnement virtuel
# On utilise .dockerignore pour gérer ces exclusions
COPY . .

EXPOSE 5000

# Lancer l'application Flask avec gunicorn en pseudo serveur web pour ne pas qu'elle tombe aussitôt
# Sinon on ne pourrait pas faire les tests d'intégration
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.app:app"]