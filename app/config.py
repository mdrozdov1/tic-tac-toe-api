import os
from logging import INFO

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
LOG_LEVEL = os.getenv("LOG_LEVEL", INFO)
LOG_FILE = os.getenv("LOG_FILE", "app.log")
APP_NAME = os.getenv("APP_NAME", "Tic-Tac-Toe")