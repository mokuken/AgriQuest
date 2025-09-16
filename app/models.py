from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# db instance used by app.__init__
db = SQLAlchemy()


class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)
	# personal goals
	daily_goal = db.Column(db.Integer, nullable=False, default=1)
	weekly_goal = db.Column(db.Integer, nullable=False, default=5)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


class Teacher(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)

	# relationship: a teacher may have many quizzes
	quizzes = db.relationship('Quiz', backref='teacher', lazy=True)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


# New models for quizzes
class Subject(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True, nullable=False)
	code = db.Column(db.String(20), unique=True)
	description = db.Column(db.Text)
	category = db.Column(db.String(50))
	grade_level = db.Column(db.String(20))
	quizzes = db.relationship('Quiz', backref='subject', lazy=True)


class Quiz(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	description = db.Column(db.Text)
	time_limit = db.Column(db.Integer, default=0)  # minutes
	difficulty = db.Column(db.String(50))
	teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
	subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
	questions = db.relationship('Question', backref='quiz', cascade='all, delete-orphan', lazy=True)
	created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


class Question(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
	type = db.Column(db.String(20), nullable=False)  # 'mc' or 'tf'
	text = db.Column(db.Text, nullable=False)
	# For MC questions, store the correct option key (A/B/C/D). For TF, store 'True'/'False'.
	correct_answer = db.Column(db.String(10), nullable=False)
	options = db.relationship('Option', backref='question', cascade='all, delete-orphan', lazy=True)


class Option(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
	key = db.Column(db.String(5), nullable=False)  # 'A','B','C','D' or other
	text = db.Column(db.Text, nullable=False)


# Records a student's attempt at a quiz
class QuizAttempt(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
	started_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
	completed_at = db.Column(db.DateTime, nullable=True)
	score = db.Column(db.Integer, nullable=True)
	percent = db.Column(db.Float, nullable=True)
	time_taken_seconds = db.Column(db.Integer, nullable=True)

	# relationship: answers for this attempt
	answers = db.relationship('AttemptAnswer', backref='attempt', cascade='all, delete-orphan', lazy=True)
	# relationship to the quiz
	quiz = db.relationship('Quiz', backref='attempts', lazy=True)


# Individual per-question answers for an attempt
class AttemptAnswer(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
	question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
	given_answer = db.Column(db.String(200))
	is_correct = db.Column(db.Boolean, nullable=True)


# Messaging models: simple Conversation between a teacher and a student and messages
class Conversation(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
	created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

	# messages relationship
	messages = db.relationship('Message', backref='conversation', cascade='all, delete-orphan', lazy=True)

	# convenience relationships to load participants
	teacher = db.relationship('Teacher', backref=db.backref('conversations', lazy='dynamic'))
	student = db.relationship('Student', backref=db.backref('conversations', lazy='dynamic'))


class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
	# sender_role: 'teacher' or 'student'
	sender_role = db.Column(db.String(20), nullable=False)
	sender_id = db.Column(db.Integer, nullable=False)
	text = db.Column(db.Text, nullable=False)
	created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
	read = db.Column(db.Boolean, nullable=False, default=False)
