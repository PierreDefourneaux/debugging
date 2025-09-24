import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.app import app as flask_app
from app.app import preprocess_from_pil, 
from PIL import Image
import numpy as np
import random

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

# Tester le fonctionnement de l'API avec une requête GET sur la page d'accueil (route "/")
def test_code200(client):
    response = client.get("/")
    assert response.status_code == 200
    
# S'assurer que le bug de format ne se répète plus et soit bien adapté à celui attendu par keras
def test_format_img_():
    n1 = random.randint(1, 1000)
    n2 = random.randint(1, 1000)
    dummy_img = Image.new("RGB", (n1, n2), color="red")
    arr = preprocess_from_pil(dummy_img)
    assert arr.shape == (1, 224, 224, 3)