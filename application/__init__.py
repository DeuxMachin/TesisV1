from flask import Flask

def create_app():
    app = Flask(__name__)

    from .routes.foldseek_routes import foldseek_bp
    app.register_blueprint(foldseek_bp)

    return app
