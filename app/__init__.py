from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# Create extension objects
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # redirect here if not logged in

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # load settings from config.py

    # Attach extensions to the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.seller import seller as seller_blueprint
    app.register_blueprint(seller_blueprint)

    from app.customer import customer as customer_blueprint
    app.register_blueprint(customer_blueprint)

    return app