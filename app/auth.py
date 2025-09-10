from flask import Blueprint, render_template

auth = Blueprint("auth", __name__)

@auth.route("/student/login")
def login_student():
    return render_template("student/login_student.html")

@auth.route("/student/register")
def register_student():
    return render_template("student/register_student.html")

@auth.route("/teacher/login")
def login_teacher():
    return render_template("teacher/login_teacher.html")

@auth.route("/teacher/register")
def register_teacher():
    return render_template("teacher/register_teacher.html")

@auth.route("/logout")
def logout():
    return render_template("logout.html")
