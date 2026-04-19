# config.py
import os
from dotenv import load_dotenv

# Force load the .env file
load_dotenv()


class Config:
    # Fetch variables from the environment
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_DSN = os.environ.get("DB_DSN")

    # A secret key is required later for our JWT authentication
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-dev-key")