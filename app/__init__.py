from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Import and register blueprints
    from .routes import main
    from .auth import auth as auth_main
    app.register_blueprint(main)
    app.register_blueprint(auth_main)

    return app
