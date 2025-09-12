from app import create_app
from app.models import Quiz, Teacher

app = create_app()

with app.test_client() as client:
    # assume teacher created earlier in previous test has email 'script_teacher@example.com'
    with app.app_context():
        teacher = Teacher.query.filter_by(email='script_teacher@example.com').first()
        print('Found teacher', teacher and teacher.id)
        teacher_id = teacher.id if teacher else None

    with client.session_transaction() as sess:
        sess['teacher_id'] = teacher_id

    resp = client.get('/teacher/quizzes')
    print('GET /teacher/quizzes status', resp.status_code)
    html = resp.get_data(as_text=True)
    # check content
    print('Contains "Teacher-linked Quiz"?', 'Teacher-linked Quiz' in html)
