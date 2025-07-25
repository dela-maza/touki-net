### app.py
import os
from flask import Flask
import settings
from db import db
from flask_migrate import Migrate
from apps.entrusted_book.views import entrusted_book_bp
from apps.client.views import client_bp
from apps.amount_document.views import amount_document_bp
from apps.property_description.views import property_bp
from apps.amount_document.filters import amount_document_type_label
from flask_wtf import CSRFProtect

app = Flask(__name__)

app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

### property_descriptionの設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.jinja_env.filters['amount_document_type_label'] = amount_document_type_label
csrf = CSRFProtect(app)  # CSRF対策有効化

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(entrusted_book_bp)
app.register_blueprint(client_bp)
app.register_blueprint(amount_document_bp)
app.register_blueprint(property_bp)

if __name__ == "__main__":
    app.run(port=5100)