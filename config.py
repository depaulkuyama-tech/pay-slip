import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change_me_in_production")
    BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))

    # Detect if running on Render
    ON_RENDER = os.environ.get("RENDER") == "true"

    if ON_RENDER:
        # Use /tmp directories on Render (writable)
        MASTER_PDF_DIR = "/tmp/Master_PDFs"
        OUTPUT_DIR = "/tmp/output"
        DB_PATH = "/tmp/users.db"
    else:
        # Local folders
        MASTER_PDF_DIR = os.path.join(BASE_DIR, "Master_PDFs")
        OUTPUT_DIR = os.path.join(BASE_DIR, "output")
        DB_PATH = os.path.join(BASE_DIR, "users.db")

# Ensure directories exist
os.makedirs(Config.MASTER_PDF_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
