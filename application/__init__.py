from flask import Flask
import base64

def create_app():
    app = Flask(__name__)

    # Registrar filtro para codificar en base64
    @app.template_filter('b64encode')
    def b64encode_filter(s):
        if isinstance(s, str):
            return base64.b64encode(s.encode()).decode()
        return base64.b64encode(s).decode()

    from application.routes.foldseek_routes import foldseek_bp
    app.register_blueprint(foldseek_bp)

    return app
