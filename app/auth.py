from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import db, Student, Teacher

auth = Blueprint("auth", __name__)

@auth.route("/student/login", methods=["GET", "POST"])
def login_student():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        student = Student.query.filter_by(email=email).first()
        if student and student.check_password(password):
            session["student_id"] = student.id
            return redirect(url_for("main.select_role"))  # Change to student dashboard route
        else:
            flash("Invalid email or password.")
    return render_template("student/login_student.html")

@auth.route("/student/register", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("student/register_student.html")
        if Student.query.filter_by(email=email).first():
            flash("Email already registered.")
            return render_template("student/register_student.html")
        student = Student(name=name, email=email)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for("auth.login_student"))
    return render_template("student/register_student.html")

@auth.route("/teacher/login", methods=["GET", "POST"])
def login_teacher():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and teacher.check_password(password):
            session["teacher_id"] = teacher.id
            return redirect(url_for("main.teacher_dashboard"))  # Change to teacher dashboard route
        else:
            flash("Invalid email or password.")
    return render_template("teacher/login_teacher.html")

@auth.route("/teacher/register", methods=["GET", "POST"])
def register_teacher():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("teacher/register_teacher.html")
        if Teacher.query.filter_by(email=email).first():
            flash("Email already registered.")
            return render_template("teacher/register_teacher.html")
        teacher = Teacher(name=name, email=email)
        teacher.set_password(password)
        db.session.add(teacher)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for("auth.login_teacher"))
    return render_template("teacher/register_teacher.html")

@auth.route("/logout")
def logout():
    return render_template("logout.html")
