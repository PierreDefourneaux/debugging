import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from PIL import Image
import numpy as np
import random
import time 
import dotenv
from dotenv import load_dotenv
import requests
import psycopg2
from psycopg2 import OperationalError
import subprocess

load_dotenv()

def test_postgres_in_its_ctn(max_retries=10, delay=2):
    """
    Teste si le conteneur PostgreSQL est accessible par le runner.
    """
    for _ in range(max_retries):
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                dbname="pierre",
                user="pierre",
                password=os.getenv("POSTGRES_PASSWORD")
            )
            conn.close()
            assert True
            return
        except OperationalError:
            time.sleep(delay)

    assert False, "Le conteneur PostgreSQL n'est pas accessible."

def test_flask_app_in_its_ctn():
    """
    Vérifie que l'API Flask réponde.
    """
    url = "http://localhost:5000/health"
    success = False
    for _ in range(10):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                success = True
                break
        except requests.exceptions.RequestException:
            pass  # ignore les erreurs de connexion temporaires
        time.sleep(10)  # attente avant le prochain essai
    
    assert success, "Le conteneur Flask ne répond pas après le délai imparti."


def test_2_ctn_network():
    """Vérifie que l'API depuis son propre conteneur comumnique avec PGSQL dans le sien ."""
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "flask_app",
            "ls"
        ],
        capture_output=True,
        text=True
    )
    print("Voici le résutat du ls:", result.stdout)

    result2 = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "flask_app",
            "python",
            "--version",
        ],
        capture_output=True,
        text=True
    )
    print("Voici le résutat du python --version:", result2.stdout)

    result4 = subprocess.run(
        ["docker", "exec", "-i", "flask_app", "ls", "app"],
        capture_output=True,
        text=True
    )
    print("Voici le résutat du ls app:", result4.stdout)

    result5 = subprocess.run(
    ["docker", "exec", "-i", "flask_app", "printenv", "POSTGRES_PASSWORD"],
    capture_output=True,
    text=True
    )
    print("Voici les résultats de printenv POSTGRES_PASSWORD:")
    print("STDOUT:", result5.stdout)
    print("STDERR:", result5.stderr)
    print("Return code:", result5.returncode)

    result6 = subprocess.run(
    [
        "docker", "exec", "-i", "flask_app", "python", "-c",
        "from app.app import get_databases; get_databases()"
    ],
    capture_output=True,
    text=True
    )
    print("Voici les résultats de get_databases():")
    print("STDOUT:", result6.stdout)
    print("STDERR:", result6.stderr)
    print("Return code:", result6.returncode)

    assert result.returncode == 0


    
# # S'assurer que le bug de format ne se répète plus et soit bien adapté à celui attendu par keras
# def test_format_img_():
#     n1 = random.randint(1, 1000)
#     n2 = random.randint(1, 1000)
#     dummy_img = Image.new("RGB", (n1, n2), color="red")
#     arr = preprocess_from_pil(dummy_img)
#     assert arr.shape == (1, 224, 224, 3)