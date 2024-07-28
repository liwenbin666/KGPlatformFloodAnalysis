from flask import Flask
from applications.view import init_bp
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(app, resources=r'/*')

    init_bp(app)

    return app
