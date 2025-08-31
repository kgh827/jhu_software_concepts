from flask import Blueprint, render_template

#this is a python file that utilizes the flask blueprint file to help set up 
# the general structure and path routing for each page in the website
bp = Blueprint("pages", __name__)

@bp.route("/")
def home():
    return render_template("pages/home.html")

@bp.route("/interests")
def interests():
    return render_template("pages/interests.html")

@bp.route("/contact")
def contact():
    return render_template("pages/contact.html")

@bp.route("/projects")
def projects():
    return render_template("pages/projects.html")