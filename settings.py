### settings.py
import os

DB_INFO = {
    'user': os.environ.get('DB_USER', 'onitsuka'),
    'password': os.environ.get('DB_PASS', ''),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'name': os.environ.get('DB_NAME', 'entrusted_book'),
}

SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{DB_INFO['user']}:{DB_INFO['password']}@{DB_INFO['host']}/{DB_INFO['name']}"

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
SQLALCHEMY_TRACK_MODIFICATIONS = False