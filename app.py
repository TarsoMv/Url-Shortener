from flask import Flask
from flask_jwt_extended import JWTManager
from config import config
from extensions import db
from views.views import views_bp
from users.users import users_bp
from auth.auth import auth_bp
from stats.stats import stats_bp
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.register_blueprint(views_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(stats_bp)
    app.config.from_object(config)
    jwt = JWTManager(app)
    db.init_app(app)

    return app

app = create_app()

#poetry run flask --app app run --debug
