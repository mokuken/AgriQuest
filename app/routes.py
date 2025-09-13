from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash

from .models import db, Subject, Quiz, Question, Option, Teacher
from .models import Student

main = Blueprint("main", __name__)


@main.route("/")
def select_role():
    return render_template("select_role.html")

@main.route("/student/dashboard")
def student_dashboard():
    # show available quizzes from all teachers (most recent first)
    from .models import Quiz, Teacher
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).limit(10).all()
    # eager load teacher info if available
    # template will handle missing teacher gracefully
    return render_template("student/dashboard.html", quizzes=quizzes)


@main.route("/student/quizzes")
def student_quizzes():
    # show all available quizzes for students (most recent first)
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template("student/quizzes.html", quizzes=quizzes)

@main.route('/student/quizzes/take/<int:quiz_id>', methods=["GET", "POST"])
def student_take_quiz(quiz_id):
    # GET: render quiz for student to take
    if request.method == 'GET':
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('main.student_quizzes'))
        # Render template with quiz and questions/options
        return render_template('student/take_quiz.html', quiz=quiz)

    # POST: grade submission (expect JSON payload with answers)
    # Payload format: { "answers": { "<question_id>": "<answer>", ... } }
    data = request.get_json() or {}
    answers = data.get('answers', {})
    # optional elapsed time (seconds) from client
    time_taken_seconds = data.get('time_taken_seconds')
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    total = len(quiz.questions)
    correct_count = 0
    details = []
    for q in quiz.questions:
        qid = str(q.id)
        given = answers.get(qid)
        is_correct = False
        # normalize True/False
        if q.type == 'tf':
            # Accept boolean or string
            if isinstance(given, bool):
                given_norm = 'True' if given else 'False'
            else:
                given_norm = str(given)
            is_correct = given_norm == q.correct_answer
        else:
            # mc: compare string keys (A/B/C...)
            if given is not None:
                is_correct = str(given).strip() == str(q.correct_answer).strip()

        if is_correct:
            correct_count += 1

        details.append({
            "question_id": q.id,
            "given": given,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
        })

    score = correct_count
    percent = (score / total * 100) if total > 0 else 0
    result = {
        "quiz_id": quiz.id,
        "total_questions": total,
        "correct": score,
        "percent": percent,
        "details": details,
    }
    # attach human-friendly time if provided
    if isinstance(time_taken_seconds, int) or (isinstance(time_taken_seconds, float)):
        secs = int(time_taken_seconds)
        mm = secs // 60
        ss = secs % 60
        result['time_taken_seconds'] = secs
        result['time_taken'] = f"{mm:02d}:{ss:02d}"
    # store last result in session for display on results page
    try:
        session['last_quiz_result'] = result
    except Exception:
        # if session can't store (very large), just return result JSON
        return jsonify(result), 200

    return jsonify({"redirect": url_for('main.student_quiz_results')}), 200

@main.route("/student/quizzes/results")
def student_quiz_results():
    # display the most recent quiz result stored in session (one-off)
    result = session.pop('last_quiz_result', None)
    quiz = None
    counts = {
        'correct': 0,
        'incorrect': 0,
        'unanswered': 0,
    }
    if result:
        quiz_id = result.get('quiz_id')
        if quiz_id:
            quiz = Quiz.query.filter_by(id=quiz_id).first()
        details = result.get('details', []) or []
        total = result.get('total_questions', 0)
        correct = result.get('correct', 0)
        unanswered = 0
        for d in details:
            given = d.get('given')
            if given is None or (isinstance(given, str) and given.strip() == ''):
                unanswered += 1
        incorrect = max(0, total - correct - unanswered)
        counts['correct'] = correct
        counts['incorrect'] = incorrect
        counts['unanswered'] = unanswered

    return render_template("student/quiz_results.html", quiz=quiz, result=result, counts=counts)

@main.route("/teacher/dashboard")
def teacher_dashboard():
    teacher_id = session.get('teacher_id')
    recent_quizzes = []
    if teacher_id:
        recent_quizzes = (
            Quiz.query.filter_by(teacher_id=teacher_id)
            .order_by(Quiz.id.desc())
            .limit(5)
            .all()
        )
    return render_template("teacher/dashboard.html", recent_quizzes=recent_quizzes)


@main.route("/teacher/subjects")
def teacher_subjects():
    subjects = Subject.query.all()
    return render_template("teacher/subjects.html", subjects=subjects)


@main.route("/teacher/subjects/create", methods=["GET", "POST"])
def teacher_create_subject():
    if request.method == "GET":
        return render_template("teacher/create_subject.html")
    # POST: create subject from modal
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    name = data.get('name')
    code = data.get('code')
    description = data.get('description')
    category = data.get('category')
    grade_level = data.get('grade_level')
    if not name:
        return jsonify({"error": "Subject name required"}), 400
    # Check for duplicate
    if Subject.query.filter_by(name=name).first():
        return jsonify({"error": "Subject already exists"}), 400
    subject = Subject(
        name=name,
        code=code,
        description=description,
        category=category,
        grade_level=grade_level
    )
    db.session.add(subject)
    db.session.commit()
    return jsonify({"status": "success", "subject_id": subject.id}), 201


@main.route("/teacher/quizzes")
def teacher_quizzes():
    from .models import Quiz
    teacher_id = session.get('teacher_id')
    quizzes = []
    if teacher_id:
        quizzes = Quiz.query.filter_by(teacher_id=teacher_id).order_by(Quiz.id.desc()).all()
    return render_template("teacher/quizzes.html", quizzes=quizzes)


@main.route("/teacher/quizzes/create", methods=["GET", "POST"])
def teacher_create_quiz():
    if request.method == "GET":
        subjects = Subject.query.all()
        return render_template("teacher/create_quiz.html", subjects=subjects)

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

    # ensure a teacher is logged in
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        return jsonify({"error": "Authentication required: teacher must be logged in"}), 401

    try:
        # get or create subject
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.session.add(subject)
            db.session.flush()

        quiz = Quiz(title=title, description=description, time_limit=time_limit or 0, difficulty=difficulty, subject=subject, teacher_id=teacher_id)
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

@main.route("/teacher/settings")
def teacher_settings():
    teacher_id = session.get('teacher_id')
    teacher = None
    if teacher_id:
        teacher = Teacher.query.filter_by(id=teacher_id).first()
    return render_template("teacher/settings.html", teacher=teacher)


@main.route('/teacher/settings/update_info', methods=['POST'])
def teacher_update_info():
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Authentication required.', 'error')
        return redirect(url_for('auth.login_teacher'))
    teacher = Teacher.query.filter_by(id=teacher_id).first()
    if not teacher:
        flash('Teacher not found.', 'error')
        return redirect(url_for('auth.login_teacher'))

    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        flash('Name and email are required.', 'error')
        return redirect(url_for('main.teacher_settings'))

    # check for email collision
    existing = Teacher.query.filter(Teacher.email == email, Teacher.id != teacher.id).first()
    if existing:
        flash('Email already in use by another account.', 'error')
        return redirect(url_for('main.teacher_settings'))

    teacher.name = name
    teacher.email = email
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('main.teacher_settings'))


@main.route('/teacher/settings/update_password', methods=['POST'])
def teacher_update_password():
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Authentication required.', 'error')
        return redirect(url_for('auth.login_teacher'))
    teacher = Teacher.query.filter_by(id=teacher_id).first()
    if not teacher:
        flash('Teacher not found.', 'error')
        return redirect(url_for('auth.login_teacher'))

    current = request.form.get('current_password')
    new = request.form.get('new_password')
    confirm = request.form.get('confirm_password')
    if not current or not new or not confirm:
        flash('Please fill out all password fields.', 'error')
        return redirect(url_for('main.teacher_settings'))
    if not teacher.check_password(current):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('main.teacher_settings'))
    if new != confirm:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('main.teacher_settings'))
    teacher.set_password(new)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('main.teacher_settings'))


@main.route('/teacher/settings/delete_account', methods=['POST'])
def teacher_delete_account():
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Authentication required.', 'error')
        return redirect(url_for('auth.login_teacher'))
    teacher = Teacher.query.filter_by(id=teacher_id).first()
    if not teacher:
        flash('Teacher not found.', 'error')
        return redirect(url_for('auth.login_teacher'))

    # Optional: confirm via password
    password = request.form.get('confirm_password')
    if password and not teacher.check_password(password):
        flash('Password confirmation incorrect.', 'error')
        return redirect(url_for('main.teacher_settings'))

    # delete teacher and logout
    db.session.delete(teacher)
    db.session.commit()
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('auth.login_teacher'))


# Edit quiz route
@main.route("/teacher/quizzes/edit/<int:quiz_id>", methods=["GET", "POST"])
def teacher_edit_quiz(quiz_id):
    teacher_id = session.get('teacher_id')
    quiz = Quiz.query.filter_by(id=quiz_id, teacher_id=teacher_id).first()
    if not quiz:
        flash("Quiz not found or access denied.", "error")
        return redirect(url_for('main.teacher_quizzes'))

    if request.method == "GET":
        return render_template("teacher/create_quiz.html", quiz=quiz, edit_mode=True)

    # POST: update quiz
    data = request.get_json() or request.form
    quiz.title = data.get('title', quiz.title)
    quiz.description = data.get('description', quiz.description)
    quiz.time_limit = int(data.get('time_limit', quiz.time_limit))
    quiz.difficulty = data.get('difficulty', quiz.difficulty)
    subject_name = data.get('subject')
    if subject_name:
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.session.add(subject)
            db.session.flush()
        quiz.subject = subject

    # Update questions
    questions = data.get('questions', [])
    # Remove old questions/options
    for q in quiz.questions:
        for opt in q.options:
            db.session.delete(opt)
        db.session.delete(q)
    db.session.flush()

    # Add new questions/options
    for q in questions:
        qtype = q.get('type')
        qtext = q.get('text')
        correct = q.get('correct')
        opts = q.get('options', [])
        question = Question(quiz=quiz, type=qtype, text=qtext, correct_answer=str(correct))
        db.session.add(question)
        db.session.flush()
        if qtype == 'mc':
            for opt in opts:
                key = opt.get('key')
                text = opt.get('text')
                if key and text is not None:
                    option = Option(question=question, key=key, text=text)
                    db.session.add(option)

    db.session.commit()
    if request.is_json:
        return jsonify({"status": "success", "quiz_id": quiz.id}), 200
    else:
        flash("Quiz updated successfully!", "success")
        return redirect(url_for('main.teacher_quizzes'))


# Student settings (mirror teacher settings)
@main.route("/student/settings")
def student_settings():
    student_id = session.get('student_id')
    student = None
    if student_id:
        student = Student.query.filter_by(id=student_id).first()
    return render_template("student/settings.html", student=student)


@main.route('/student/settings/update_info', methods=['POST'])
def student_update_info():
    student_id = session.get('student_id')
    if not student_id:
        flash('Authentication required.', 'error')
        return redirect(url_for('auth.login_student'))
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('auth.login_student'))

    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        flash('Name and email are required.', 'error')
        return redirect(url_for('main.student_settings'))

    # check for email collision
    existing = Student.query.filter(Student.email == email, Student.id != student.id).first()
    if existing:
        flash('Email already in use by another account.', 'error')
        return redirect(url_for('main.student_settings'))

    student.name = name
    student.email = email
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('main.student_settings'))


@main.route('/student/settings/update_password', methods=['POST'])
def student_update_password():
    student_id = session.get('student_id')
    if not student_id:
        flash('Authentication required.', 'error')
        return redirect(url_for('auth.login_student'))
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('auth.login_student'))

    current = request.form.get('current_password')
    new = request.form.get('new_password')
    confirm = request.form.get('confirm_password')
    if not current or not new or not confirm:
        flash('Please fill out all password fields.', 'error')
        return redirect(url_for('main.student_settings'))
    if not student.check_password(current):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('main.student_settings'))
    if new != confirm:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('main.student_settings'))
    student.set_password(new)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('main.student_settings'))


@main.route('/student/settings/delete_account', methods=['POST'])
def student_delete_account():
    student_id = session.get('student_id')
    if not student_id:
        flash('Authentication required.', 'error')
        return redirect(url_for('auth.login_student'))
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('auth.login_student'))

    # Optional: confirm via password
    password = request.form.get('confirm_password')
    if password and not student.check_password(password):
        flash('Password confirmation incorrect.', 'error')
        return redirect(url_for('main.student_settings'))

    # delete student and logout
    db.session.delete(student)
    db.session.commit()
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('auth.login_student'))
