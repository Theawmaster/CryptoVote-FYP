import os
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:5010")

SQLALCHEMY_DATABASE_URI = "postgresql://theawmaster@localhost:5432/cryptovote"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.urandom(32)
