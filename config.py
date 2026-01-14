import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change_me_in_production")
    BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))

    # Folder where all master PDFs for pay periods are stored
    MASTER_PDF_DIR = os.path.join(BASE_DIR, "Master_PDFs")

    # Output folder for extracted employee PDFs
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")

    # Database path
    DB_PATH = os.path.join(BASE_DIR, "users.db")

# Ensure the output folder exists
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
os.makedirs(Config.MASTER_PDF_DIR, exist_ok=True)  # <-- ensure Master_PDFs exists
