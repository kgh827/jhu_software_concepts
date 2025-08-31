#import flask module for site build
from flask import Flask

#import pages module
from . import pages

#creates new flask instance when called
def create_app():
    app = Flask(__name__)
    app.register_blueprint(pages.bp) #calls/registers blueprint of site with the app being instantiated
    return app #returns app so it can run
