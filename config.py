import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cybersec-dashboard-secret-key-2024")
    DATABASE = os.path.join(BASE_DIR, "cybersec.db")
    JWT_EXPIRATION_HOURS = 12
    # Flask serve static frontend from ../frontend
    FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
