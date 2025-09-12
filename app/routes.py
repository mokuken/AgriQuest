from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.route("/")
def select_role():
    return render_template("select_role.html")

@main.route("/teacher/dashboard")
def teacher_dashboard():
    return render_template("teacher/dashboard.html")

@main.route("/teacher/subjects")
def teacher_subjects():
    return render_template("teacher/subjects.html")

@main.route("/teacher/subjects/create")
def teacher_create_subject():
    return render_template("teacher/create_subject.html")

@main.route("/teacher/quizzes")
def teacher_quizzes():
    return render_template("teacher/quizzes.html")

@main.route("/teacher/quizzes/create")
def teacher_create_quiz():
    return render_template("teacher/create_quiz.html")

@main.route("/teacher/students")
def teacher_students():
    return render_template("teacher/students.html")
