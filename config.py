import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change_me_in_production")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Correct Render detection
    ON_RENDER = os.environ.get("RENDER_SERVICE_ID") is not None

    if ON_RENDER:
        MASTER_PDF_DIR = "/tmp/Master_PDFs"
        OUTPUT_DIR = "/tmp/output"
        DB_PATH = "/tmp/users.db"
    else:
        MASTER_PDF_DIR = os.path.join(BASE_DIR, "Master_PDFs")
        OUTPUT_DIR = os.path.join(BASE_DIR, "output")
        DB_PATH = os.path.join(BASE_DIR, "users.db")

# Ensure directories exist
os.makedirs(Config.MASTER_PDF_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
