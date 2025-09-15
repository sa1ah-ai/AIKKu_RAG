from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ENUM

db = SQLAlchemy()

# Define enums
user_type_enum = ENUM('student', 'admin', name='user_type_enum', create_type=False)
language_enum = ENUM('English', 'Arabic', name='language_enum', create_type=False)
account_status_enum = ENUM('active', 'suspended', 'deleted', name='account_status_enum', create_type=False)
sender_type_enum = ENUM('student', 'system', name='sender_type_enum', create_type=False)

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    user_type = db.Column(user_type_enum, nullable=False)
    first_name = db.Column(db.String(20))
    last_name = db.Column(db.String(20))
    profile_picture_path = db.Column(db.String(255))
    language_preference = db.Column(language_enum, default='English')
    account_status = db.Column(account_status_enum, default='active')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    student = db.relationship('Student', uselist=False, back_populates='user')
    admin = db.relationship('Admin', uselist=False, back_populates='user')

class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    university_id = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(100))
    year_of_study = db.Column(db.Integer)

    # Relationships
    user = db.relationship('User', back_populates='student')
    chat_sessions = db.relationship('ChatSession', back_populates='student')
    feedbacks = db.relationship('Feedback', back_populates='student')

class Admin(db.Model):
    __tablename__ = 'admins'
    admin_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    access_level = db.Column(db.Integer)

    # Relationships
    user = db.relationship('User', back_populates='admin')
    training_data = db.relationship('TrainingData', back_populates='admin')

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'))
    session_title = db.Column(db.String(100))
    language_used = db.Column(language_enum, default='English')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_activity = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    student = db.relationship('Student', back_populates='chat_sessions')
    messages = db.relationship('ChatMessage', back_populates='session')
    feedbacks = db.relationship('Feedback', back_populates='session')

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    message_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.session_id', ondelete='CASCADE'))
    sender_type = db.Column(sender_type_enum)
    message_text = db.Column(db.Text)
    is_arabic = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    session = db.relationship('ChatSession', back_populates='messages')

class Feedback(db.Model):
    __tablename__ = 'feedback'
    feedback_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.session_id', ondelete='CASCADE'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='SET NULL'))
    rating = db.Column(db.Integer)
    feedback_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    session = db.relationship('ChatSession', back_populates='feedbacks')
    student = db.relationship('Student', back_populates='feedbacks')

class TrainingData(db.Model):
    __tablename__ = 'training_data'
    data_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.admin_id', ondelete='SET NULL'))
    input_text = db.Column(db.Text)
    output_text = db.Column(db.Text)
    language = db.Column(language_enum)
    category = db.Column(db.String)
    added_at = db.Column(db.DateTime, server_default=db.func.now())
    is_approved = db.Column(db.Boolean, default=False)

    # Relationships
    admin = db.relationship('Admin', back_populates='training_data')
