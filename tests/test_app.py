import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

# Assurez-vous que la requête GET sur la page d'accueil (route "/") renvoie bien le code HTTP 200.
def test_code200(client):
    response = client.get("/")
    assert response.status_code == 200
    
# S'assurer que le bug de format ne se répète plus et soit bien adapté à celui attendu par keras
def test_format_img_():
    from app import preprocess_from_pil
    from PIL import Image
    import numpy as np
    import random
    
    n1 = random.randint(1, 1000)
    n2 = random.randint(1, 1000)

    dummy_img = Image.new("RGB", (n1, n2), color="red")
    arr = preprocess_from_pil(dummy_img)

    assert arr.shape == (1, 224, 224, 3)






# # Assurez vous que la forme de sortie du vectorizer est cohérente avec la forme
# #  d'entrée du classifieur (Logistic regression)
# def test_vectorizer_shape(): # pas besoin de client ici car on n'utilise pas de route
#     from app import vectorizer, model
#     assert vectorizer.get_feature_names_out().shape[0] == model.n_features_in_

# # Assurez-vous que la probabilité de la prédiction de la classe prédite
# # est comprise entre 0 et 1 (en sortie de predict_proba() du classifieur)
# def test_check_classifier_output():
#     from app import vectorizer, model
#     transformed_phrase = vectorizer.transform(["Ceci est une phrase test"])
#     probabilities = model.predict_proba(transformed_phrase)[0]
#     assert probabilities.sum() == 1

# # Assurez-vous que la requête GET sur la page d'accueil (route "/") renvoie bien le code HTTP 200.
# def test_code200(client):
#     response = client.get("/")
#     assert response.status_code == 200

# # Assurez-vous que le classifieur est bien une instance de 
# # la classe LogisticRegression (classe importée depuis sklearn.linear_model)
# def test_model_LogReg_class():
#     from app import model
#     assert isinstance(model, LogisticRegression)