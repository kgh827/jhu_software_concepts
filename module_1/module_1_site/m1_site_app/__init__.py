from flask import Flask

from m1_site_app import pages

def create_app():
    app = Flask(__name__)

    app.register_blueprint(pages.bp)
    return app