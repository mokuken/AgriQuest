from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.route("/")
def select_role():
    return render_template("select_role.html")
