import os
from pathlib import Path

# --- Project Paths ---
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "database"

# Ensure runtime directories exist
for d in [DATA_DIR, LOGS_DIR, DB_DIR]:
    d.mkdir(exist_ok=True)

# Subdirectories for data
IMAGES_DIR = DATA_DIR / "images"
OVERLAYS_DIR = DATA_DIR / "overlays"
REPORTS_DIR = DATA_DIR / "reports"

for d in [IMAGES_DIR, OVERLAYS_DIR, REPORTS_DIR]:
    d.mkdir(exist_ok=True)

# --- Database ---
DB_PATH = DB_DIR / "chest_xray.db"

# --- Model Configuration ---
MODEL_PATH = MODELS_DIR / "modelo_final.keras" # Using .keras as seen in the dir
MODEL_CONFIG_PATH = MODELS_DIR / "model_config.json"

# --- App Settings ---
APP_TITLE = "ToraxIA: Diagnóstico Asistido por IA"
APP_ICON = "🩻"
