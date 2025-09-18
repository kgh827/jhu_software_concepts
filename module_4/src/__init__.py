from flask import Flask

def create_app():
    """
    Module initialization for src package.

    This file marks the directory as a Python package and can be used
    to expose top-level imports if needed.
    """
    app = Flask(__name__)
    return app
