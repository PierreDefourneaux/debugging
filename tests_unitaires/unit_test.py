import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import random
from PIL import Image
from app.app import preprocess_from_pil

# S'assurer que le bug de format ne se répète plus et soit bien adapté à celui attendu par keras
def test_preprocessed_shape_from_random_values():
    n1 = random.randint(1, 1000)
    n2 = random.randint(1, 1000)
    dummy_img = Image.new("RGB", (n1, n2), color="red")
    arr = preprocess_from_pil(dummy_img)
    assert arr.shape == (1, 224, 224, 3)