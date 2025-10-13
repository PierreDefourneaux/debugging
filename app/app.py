"""
Module principal de l'application Flask pour la classification d'images.

Ce module contient :
- La configuration de Flask et SQLAlchemy pour la base PostgreSQL.
- Le chargement du modèle Keras pour la prédiction d'images.
- La configuration du logging et alerting par mail.
- Les routes Flask pour :
    - la page d'accueil et l'upload d'image ("/")
    - la prédiction d'image ("/predict")
    - le feedback utilisateur ("/feedback")
- Les fonctions utilitaires pour :
    - vérifier les extensions de fichiers autorisées
    - convertir les images PIL en Data URL
    - prétraiter les images pour le modèle Keras

Notes :
- Les templates HTML sont dans `templates/`.
- Dashboard de monitoring Flask intégré via `flask_monitoringdashboard`.
"""

import os
import io
import base64
import logging
from logging.handlers import SMTPHandler

os.environ["KERAS_BACKEND"] = "torch"
import keras
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import flask_monitoringdashboard as dashboard
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
MDP_GOOGLE = os.getenv("MDP_GOOGLE")
POSTGRES_PASSWORD = os.getenv("MDP_GOOGLE")

# --------------------------------------- Config logging -----------------------------------------
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
# la variable spéciale __file__ contient le chemin du fichier Python en  cours d’exécution
LOG_FILE = os.path.join(LOG_DIR, "app.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # Écrit dans log/app.log
        logging.StreamHandler()])  # Continue d'afficher dans la console (stdout/stderr)
logger = logging.getLogger(__name__)

# ---------------- Config alerting mail ----------------
mail_handler = SMTPHandler(
    mailhost=("smtp.gmail.com", 587),
    fromaddr="pierre.defourneaux@gmail.com",
    toaddrs=["pierre.defourneaux@gmail.com"],
    subject=" CRITICAL error in Flask app",
    credentials=("pierre.defourneaux@gmail.com", MDP_GOOGLE),
    secure=() # secure de SMTPHandler sert à activer une connexion chiffrée avec le serveur SMTP
)
mail_handler.setLevel(logging.CRITICAL) # déclencher à partir de critical
logger.addHandler(mail_handler)
logger.critical("Ceci est un test CRITICAL pour recevoir un mail")
logger.info(f"cwd pour savoir comment atteindre le config file cfg :{os.getcwd()}")

# ---------------- Config ----------------
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}
CLASSES = ['desert', 'forest', 'meadow', 'mountain']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://pierre:{POSTGRES_PASSWORD}@db:5432/pierre"
db = SQLAlchemy(app)

logger.info(f"""PATH EXIST ?{os.path.exists('/home/pierre/debugger/config.cfg')}""")
dashboard.config.init_from(file='/home/pierre/debugger/config.cfg')

logger.info(f"Dashboard username configuré: {dashboard.config.username}")
logger.info(f"Dashboard password configuré: {dashboard.config.password}")

# ---------------- Model ----------------
MODEL_PATH = "app/models/final_cnn.keras"
try:
    model = keras.saving.load_model(MODEL_PATH, compile=False)
    model_input_shape = model.input_shape
    model_height = model_input_shape[1]
    model_width =  model_input_shape[2]
    logger.debug(f"model_input_shape : {model_input_shape}")
    logger.debug(f"Input model_height : {model_height}")
    logger.debug(f"Input model_width : {model_width}")
except Exception as e:
    # insersion d'un alerting déclenché par un logger de niveau critical
    logger.critical(f"Impossible de charger le modèle {MODEL_PATH}: {e}", exc_info=True)
    raise # faire remonter l'erreur et arreter l'app maintenant


def get_databases():
    with app.app_context():
        result = db.session.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        for row in result:
            logger.info(f"""Voila une base de PGSQL :{row[0]}""")
if __name__ == "__main__":
    get_databases()

# ---------------- Utils ----------------
def allowed_file(filename: str) -> bool:
    """Vérifie si le nom de fichier possède une extension autorisée.
    La vérification est **insensible à la casse** et ne regarde que la sous-chaîne
    après le dernier point. Dépend de la constante globale `ALLOWED_EXT`.

    Args:
        filename: Nom du fichier soumis (ex. "photo.PNG").

    Returns:
        True si l’extension (ex. "png", "jpg") est dans `ALLOWED_EXT`, sinon False.

    Examples:
        >>> ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}
        >>> allowed_file("img.JPG")
        True
        >>> allowed_file("archive.tar.gz")
        False
    """
    logger.info(f"input passé dans allowed_file : {allowed_file}")
    logger.info(f"""allowed_file:
        {"." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT}""")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def to_data_url(pil_img: Image.Image, fmt="JPEG") -> str:
    """Convertit une image PIL en Data URL base64 affichable dans un <img src="...">.
    L’image est encodée en mémoire (sans I/O disque), sérialisée en base64, puis
    encapsulée comme `data:<mime>;base64,<payload>`. Le type MIME est déduit de `fmt`.

    Args:
        pil_img: Image PIL à encoder.
        fmt: Format d’encodage PIL (ex. "JPEG", "PNG"). Par défaut "JPEG".

    Returns:
        Chaîne Data URL prête à être insérée dans une balise <img>.

    Raises:
        ValueError: si la sauvegarde PIL échoue pour le format demandé.

    Examples:
        >>> url = to_data_url(Image.new("RGB", (10, 10), "red"), fmt="PNG")
        >>> url.startswith("data:image/png;base64,")
        True
    """
    buffer = io.BytesIO()
    pil_img.save(buffer, format=fmt)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    mime = "image/jpeg" if fmt.upper() == "JPEG" else f"image/{fmt.lower()}"
    return f"data:{mime};base64,{b64}"

def preprocess_from_pil(pil_img: Image.Image) -> np.ndarray:
    """Prépare une image PIL pour une prédiction Keras (normalisation + batch).
    Convertit en RGB, normalise en [0, 1] (float32) et ajoute l’axe batch.

    Args:
        pil_img: Image PIL source.

    Returns:
        np.ndarray de forme (1, H, W, 3), dtype float32, valeurs ∈ [0, 1].
    """
    img = pil_img.convert("RGB")
    # REDIMENSIONER ICI POUR FIX LE BUG
    img = img.resize((model_width, model_height), Image.Resampling.LANCZOS)
    img_array = np.asarray(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# ---------------- Routes ----------------
@app.route("/", methods=["GET"])
def index():
    """Affiche la page d’upload.

    Returns:
        Réponse HTML rendant le template "upload.html".
    """
    return render_template("upload.html")



@app.route("/predict", methods=["POST"])
def predict():
    """Traite l’upload, exécute la prédiction et affiche le résultat.

    Attendu: une requête `multipart/form-data` avec le champ `file`.
    Étapes:
      1) Validation de présence et d’extension du fichier.
      2) Lecture du contenu en mémoire et ouverture en PIL.
      3) Prétraitement -> tenseur (1, H, W, 3).
      4) Prédiction Keras -> probas, top-1 (label, confiance).
      5) Encodage de l’image en Data URL et rendu du template résultat.

    Redirects:
        - Redirige vers "/" si le fichier est manquant ou invalide.

    Returns:
        Réponse HTML rendant "result.html" avec:
        - `image_data_url` : image soumise encodée (data:image/jpeg;base64,+chaine base64),
        - `base64_only` : seulement la chaine base 64
        - `predicted_label` : classe prédite (str),
        - `confidence` : score softmax (float),
        - `classes` : liste des classes (pour les boutons).
    """

    if "file" not in request.files:
        return redirect("/")

    file = request.files["file"]
    if file.filename == "" or not allowed_file(secure_filename(file.filename)):
        return redirect("/")

    raw = file.read()
    pil_img = Image.open(io.BytesIO(raw))
    img_array = preprocess_from_pil(pil_img)

    logger.info(f"Type de img_array ={type(img_array)})")
    logger.info(f"Shape de img_array ={img_array.shape}")
    probs = model.predict(img_array, verbose=0)[0]
    cls_idx = int(np.argmax(probs))
    label = CLASSES[cls_idx]
    conf = float(probs[cls_idx])

    image_data_url = to_data_url(pil_img, fmt="JPEG")
    base64_only = image_data_url.split(',')[1]

    return render_template("result.html",
        image_data_url=image_data_url,
        base64_only = base64_only,
        predicted_label=label,
        confidence=conf,
        classes=CLASSES)

@app.route("/feedback", methods=["GET"])
def feedback():
    """Affiche la page de confirmation de feedback (placeholder).

    Returns:
        Réponse HTML rendant le template "feedback_ok.html".
    """
    base64_only = request.form.get('base64_data', '')
    return render_template("feedback_ok.html",base64_only = base64_only)

dashboard.bind(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
