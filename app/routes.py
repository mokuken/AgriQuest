from flask import Blueprint, render_template, request, jsonify

from .models import db, Subject, Quiz, Question, Option

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


@main.route("/teacher/quizzes/create", methods=["GET", "POST"])
def teacher_create_quiz():
    if request.method == "GET":
        return render_template("teacher/create_quiz.html")

    # POST: expect JSON payload describing quiz
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    title = data.get('title')
    subject_name = data.get('subject')
    time_limit = data.get('time_limit')
    difficulty = data.get('difficulty')
    description = data.get('description')
    questions = data.get('questions', [])

    if not title or not subject_name:
        return jsonify({"error": "Missing required fields: title and subject"}), 400

    try:
        # get or create subject
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.session.add(subject)
            db.session.flush()

        quiz = Quiz(title=title, description=description, time_limit=time_limit or 0, difficulty=difficulty, subject=subject)
        db.session.add(quiz)
        db.session.flush()

        for q in questions:
            qtype = q.get('type')
            qtext = q.get('text')
            correct = q.get('correct')
            opts = q.get('options', [])
            if not qtype or not qtext or correct is None:
                raise ValueError('Invalid question payload')

            question = Question(quiz=quiz, type=qtype, text=qtext, correct_answer=str(correct))
            db.session.add(question)
            db.session.flush()

            # options for MC questions
            if qtype == 'mc':
                for opt in opts:
                    key = opt.get('key')
                    text = opt.get('text')
                    if key and text is not None:
                        option = Option(question=question, key=key, text=text)
                        db.session.add(option)

        db.session.commit()
        return jsonify({"status": "success", "quiz_id": quiz.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/teacher/students")
def teacher_students():
    return render_template("teacher/students.html")
