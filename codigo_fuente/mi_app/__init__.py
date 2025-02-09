from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = 'key_dwes_2023'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://reto2:reto2@localhost/reto2?port=5433'
db = SQLAlchemy(app)

from  mi_app.catalogo.vistas import catalog
app.register_blueprint(catalog)
with app.app_context():
    db.create_all()

