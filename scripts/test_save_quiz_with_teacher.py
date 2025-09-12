from app import create_app
from app.models import db, Teacher, Quiz

app = create_app()

with app.app_context():
    # ensure clean teacher for test
    t = Teacher.query.filter_by(email='script_teacher@example.com').first()
    if t:
        db.session.delete(t)
        db.session.commit()

    teacher = Teacher(name='Script Teacher', email='script_teacher@example.com')
    teacher.set_password('password')
    db.session.add(teacher)
    db.session.commit()

    teacher_id = teacher.id

with app.test_client() as client:
    # set the session teacher_id
    with client.session_transaction() as sess:
        sess['teacher_id'] = teacher_id

    payload = {
        "title": "Teacher-linked Quiz",
        "subject": "Agriculture",
        "time_limit": 15,
        "difficulty": "Intermediate",
        "description": "Quiz linked to teacher",
        "questions": [
            {"type": "mc", "text": "Which is a crop?", "correct": "A", "options": [
                {"key": "A", "text": "Rice"},
                {"key": "B", "text": "Laptop"},
                {"key": "C", "text": "Phone"},
                {"key": "D", "text": "Car"}
            ]}
        ]
    }
    resp = client.post('/teacher/quizzes/create', json=payload)
    print('POST STATUS', resp.status_code, resp.get_json())

    # verify quiz stored with teacher_id
    with app.app_context():
        q = Quiz.query.filter_by(title='Teacher-linked Quiz').first()
        if q:
            print('SAVED QUIZ ID', q.id, 'teacher_id', q.teacher_id)
        else:
            print('Quiz not found')
