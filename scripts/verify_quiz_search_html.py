from app import create_app
from app.models import Teacher

app = create_app()
with app.test_client() as client:
    with app.app_context():
        t = Teacher.query.filter_by(email='script_teacher@example.com').first()
        tid = t.id if t else None
    with client.session_transaction() as sess:
        sess['teacher_id'] = tid
    r = client.get('/teacher/quizzes')
    h = r.get_data(as_text=True)
    print('has-search-input', 'id="quiz-search"' in h)
    print('has-data-attr', 'data-title=' in h)
