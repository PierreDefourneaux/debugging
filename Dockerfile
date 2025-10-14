# Image de base Python légère
FROM python:3.10-slim

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Copier uniquement les fichiers nécessaires
# On copie d'abord requirements.txt pour profiter du cache Docker
COPY app/requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet en excluant les dossiers cachés et l'environnement virtuel
# On utilise .dockerignore pour gérer les exclusions
COPY . .

# Exposer le port Flask
EXPOSE 5000

# Commande pour lancer l'application Flask
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.app:app"]
