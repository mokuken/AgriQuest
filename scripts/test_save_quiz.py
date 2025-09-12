from app import create_app
import json

app = create_app()

with app.test_client() as client:
    payload = {
        "title": "Test Quiz from Script",
        "subject": "Agriculture",
        "time_limit": 20,
        "difficulty": "Beginner",
        "description": "A small test quiz",
        "questions": [
            {"type": "mc", "text": "What grows on farms?", "correct": "A", "options": [
                {"key": "A", "text": "Crops"},
                {"key": "B", "text": "Computers"},
                {"key": "C", "text": "Phones"},
                {"key": "D", "text": "Cars"}
            ]}
        ]
    }
    resp = client.post('/teacher/quizzes/create', json=payload)
    print('STATUS', resp.status_code)
    print(resp.get_json())
