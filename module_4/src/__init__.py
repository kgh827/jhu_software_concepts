from flask import Flask

def create_app():
    app = Flask(__name__)
    # register blueprints, routes, etc.
    return app
