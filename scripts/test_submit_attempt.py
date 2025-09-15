from app import create_app
from app.models import db, Quiz, Student, QuizAttempt

app = create_app()
with app.app_context():
    q = Quiz.query.first()
    if not q:
        print('no quizzes in DB')
        raise SystemExit(0)

    # build a minimal answers payload: try to mark first question if available
    answers = {}
    if q.questions:
        for question in q.questions:
            # provide a deliberately empty answer to simulate skipping or choose correct if tf
            if question.type == 'tf':
                answers[str(question.id)] = 'True'
            else:
                # try to pick first option key if available
                if question.options:
                    answers[str(question.id)] = question.options[0].key
                else:
                    answers[str(question.id)] = None

    client = app.test_client()

    # ensure a student exists and set session student_id for the test client
    student = Student.query.first()
    if not student:
        student = Student(name='Test Student', email='test_student@example.com')
        student.set_password('password')
        db.session.add(student)
        db.session.commit()

    payload = {'answers': answers, 'time_taken_seconds': 5}
    # set session student_id
    with client.session_transaction() as sess:
        sess['student_id'] = student.id

    resp = client.post(f'/student/quizzes/take/{q.id}', json=payload)
    print('status', resp.status_code)
    try:
        print('body', resp.get_json())
    except Exception:
        print('body (raw)', resp.get_data(as_text=True)[:1000])

    attempts = QuizAttempt.query.filter_by(quiz_id=q.id).all()
    print('attempts found for quiz id', q.id, len(attempts))
    if attempts:
        a = attempts[-1]
        print('last attempt:', a.id, 'score', a.score, 'time', a.time_taken_seconds)
