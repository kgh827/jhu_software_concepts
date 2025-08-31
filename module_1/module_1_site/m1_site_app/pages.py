from flask import Blueprint, render_template #imports flask blueprint and render_template to use for site layout

#this is a python file that utilizes the flask blueprint file to help set up 
# the general structure and path routing for each page in the website
bp = Blueprint("pages", __name__)

#site home page link routing
@bp.route("/")
def home():
    return render_template("pages/home.html")

#site interests page link routing
@bp.route("/interests")
def interests():
    return render_template("pages/interests.html")

#site contact page link routing
@bp.route("/contact")
def contact():
    return render_template("pages/contact.html")

#site projects page link routing
@bp.route("/projects")
def projects():
    return render_template("pages/projects.html")