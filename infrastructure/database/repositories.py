from typing import List, Optional, Dict, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session
from domain.repositories import (
    UserRepository, StudentRepository, AdminRepository, 
    ChatSessionRepository, ChatMessageRepository, 
    FeedbackRepository, TrainingDataRepository
)
from domain.entities import (
    User, Student, Admin, ChatSession, ChatMessage, Feedback, 
    TrainingData, UserType, Language, SenderType, AccountStatus
)
from database.db_model import (
    User as UserModel, Student as StudentModel, Admin as AdminModel,
    ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel,
    Feedback as FeedbackModel, TrainingData as TrainingDataModel
)
from datetime import datetime


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def create(self, user: User) -> User:
        """Create a new user"""
        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            user_type=user.user_type.value,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_picture_path=user.profile_picture_path,
            language_preference=user.language_preference.value,
            account_status=user.account_status.value
        )
        self.db.session.add(user_model)
        self.db.session.commit()
        return self._to_domain(user_model)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        user_model = UserModel.query.get(user_id)
        return self._to_domain(user_model) if user_model else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_model = UserModel.query.filter_by(email=email).first()
        return self._to_domain(user_model) if user_model else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_model = UserModel.query.filter_by(username=username).first()
        return self._to_domain(user_model) if user_model else None
    
    def update(self, user: User) -> User:
        """Update user"""
        user_model = UserModel.query.get(user.user_id)
        if not user_model:
            raise ValueError(f"User with ID {user.user_id} not found")
        
        user_model.username = user.username
        user_model.email = user.email
        user_model.first_name = user.first_name
        user_model.last_name = user.last_name
        user_model.profile_picture_path = user.profile_picture_path
        user_model.language_preference = user.language_preference.value
        user_model.account_status = user.account_status.value
        
        self.db.session.commit()
        return self._to_domain(user_model)
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        user_model = UserModel.query.get(user_id)
        if user_model:
            self.db.session.delete(user_model)
            self.db.session.commit()
            return True
        return False
    
    def list_all(self, limit: Optional[int] = None) -> List[User]:
        """List all users"""
        query = UserModel.query
        if limit:
            query = query.limit(limit)
        return [self._to_domain(user) for user in query.all()]
    
    def _to_domain(self, user_model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity"""
        return User(
            user_id=user_model.user_id,
            username=user_model.username,
            email=user_model.email,
            password_hash=user_model.password_hash,
            user_type=UserType(user_model.user_type),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            profile_picture_path=user_model.profile_picture_path,
            language_preference=Language(user_model.language_preference),
            account_status=AccountStatus(user_model.account_status),
            created_at=user_model.created_at
        )


class SQLAlchemyStudentRepository(StudentRepository):
    """SQLAlchemy implementation of StudentRepository"""
    
    def __init__(self, db: SQLAlchemy, user_repo: UserRepository):
        self.db = db
        self.user_repo = user_repo
    
    def create(self, student: Student) -> Student:
        """Create a new student"""
        student_model = StudentModel(
            student_id=student.student_id,
            university_id=student.university_id,
            major=student.major,
            year_of_study=student.year_of_study
        )
        self.db.session.add(student_model)
        self.db.session.commit()
        return self._to_domain(student_model)
    
    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Get student by ID"""
        student_model = StudentModel.query.get(student_id)
        return self._to_domain(student_model) if student_model else None
    
    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        """Get student by user ID"""
        student_model = StudentModel.query.get(user_id)
        return self._to_domain(student_model) if student_model else None
    
    def update(self, student: Student) -> Student:
        """Update student"""
        student_model = StudentModel.query.get(student.student_id)
        if not student_model:
            raise ValueError(f"Student with ID {student.student_id} not found")
        
        student_model.university_id = student.university_id
        student_model.major = student.major
        student_model.year_of_study = student.year_of_study
        
        self.db.session.commit()
        return self._to_domain(student_model)
    
    def delete(self, student_id: int) -> bool:
        """Delete student"""
        student_model = StudentModel.query.get(student_id)
        if student_model:
            self.db.session.delete(student_model)
            self.db.session.commit()
            return True
        return False
    
    def list_all(self, limit: Optional[int] = None) -> List[Student]:
        """List all students"""
        query = StudentModel.query
        if limit:
            query = query.limit(limit)
        return [self._to_domain(student) for student in query.all()]
    
    def _to_domain(self, student_model: StudentModel) -> Student:
        """Convert SQLAlchemy model to domain entity"""
        user = self.user_repo.get_by_id(student_model.student_id)
        return Student(
            student_id=student_model.student_id,
            user=user,
            university_id=student_model.university_id,
            major=student_model.major,
            year_of_study=student_model.year_of_study
        )


class SQLAlchemyChatSessionRepository(ChatSessionRepository):
    """SQLAlchemy implementation of ChatSessionRepository"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def create(self, session: ChatSession) -> ChatSession:
        """Create a new chat session"""
        session_model = ChatSessionModel(
            student_id=session.student_id,
            session_title=session.session_title,
            language_used=session.language_used.value,
            created_at=session.created_at or datetime.now(),
            last_activity=session.last_activity or datetime.now()
        )
        self.db.session.add(session_model)
        self.db.session.commit()
        return self._to_domain(session_model)
    
    def get_by_id(self, session_id: int) -> Optional[ChatSession]:
        """Get chat session by ID"""
        session_model = ChatSessionModel.query.get(session_id)
        return self._to_domain(session_model) if session_model else None
    
    def get_by_student_id(self, student_id: int) -> List[ChatSession]:
        """Get chat sessions by student ID"""
        sessions = ChatSessionModel.query.filter_by(student_id=student_id).all()
        return [self._to_domain(session) for session in sessions]
    
    def update(self, session: ChatSession) -> ChatSession:
        """Update chat session"""
        session_model = ChatSessionModel.query.get(session.session_id)
        if not session_model:
            raise ValueError(f"Chat session with ID {session.session_id} not found")
        
        session_model.session_title = session.session_title
        session_model.language_used = session.language_used.value
        session_model.last_activity = session.last_activity
        
        self.db.session.commit()
        return self._to_domain(session_model)
    
    def delete(self, session_id: int) -> bool:
        """Delete chat session"""
        session_model = ChatSessionModel.query.get(session_id)
        if session_model:
            self.db.session.delete(session_model)
            self.db.session.commit()
            return True
        return False
    
    def get_active_sessions(self, student_id: int) -> List[ChatSession]:
        """Get active chat sessions for a student"""
        sessions = ChatSessionModel.query.filter_by(student_id=student_id).all()
        return [self._to_domain(session) for session in sessions if not session.is_deleted]
    
    def _to_domain(self, session_model: ChatSessionModel) -> ChatSession:
        """Convert SQLAlchemy model to domain entity"""
        return ChatSession(
            session_id=session_model.session_id,
            student_id=session_model.student_id,
            session_title=session_model.session_title,
            language_used=Language(session_model.language_used),
            created_at=session_model.created_at,
            last_activity=session_model.last_activity,
            is_deleted=getattr(session_model, 'is_deleted', False)
        )


class SQLAlchemyChatMessageRepository(ChatMessageRepository):
    """SQLAlchemy implementation of ChatMessageRepository"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new chat message"""
        message_model = ChatMessageModel(
            session_id=message.session_id,
            sender_type=message.sender_type.value,
            message_text=message.message_text,
            is_arabic=message.is_arabic,
            created_at=message.created_at or datetime.now()
        )
        self.db.session.add(message_model)
        self.db.session.commit()
        return self._to_domain(message_model)
    
    def get_by_session_id(self, session_id: int) -> List[ChatMessage]:
        """Get messages by session ID"""
        messages = ChatMessageModel.query.filter_by(session_id=session_id).order_by(ChatMessageModel.created_at).all()
        return [self._to_domain(message) for message in messages]
    
    def get_by_id(self, message_id: int) -> Optional[ChatMessage]:
        """Get message by ID"""
        message_model = ChatMessageModel.query.get(message_id)
        return self._to_domain(message_model) if message_model else None
    
    def update(self, message: ChatMessage) -> ChatMessage:
        """Update chat message"""
        message_model = ChatMessageModel.query.get(message.message_id)
        if not message_model:
            raise ValueError(f"Chat message with ID {message.message_id} not found")
        
        message_model.message_text = message.message_text
        message_model.is_arabic = message.is_arabic
        
        self.db.session.commit()
        return self._to_domain(message_model)
    
    def delete(self, message_id: int) -> bool:
        """Delete chat message"""
        message_model = ChatMessageModel.query.get(message_id)
        if message_model:
            self.db.session.delete(message_model)
            self.db.session.commit()
            return True
        return False
    
    def _to_domain(self, message_model: ChatMessageModel) -> ChatMessage:
        """Convert SQLAlchemy model to domain entity"""
        return ChatMessage(
            message_id=message_model.message_id,
            session_id=message_model.session_id,
            sender_type=SenderType(message_model.sender_type),
            message_text=message_model.message_text,
            is_arabic=message_model.is_arabic,
            created_at=message_model.created_at
        ) 


class SQLAlchemyFeedbackRepository(FeedbackRepository):
    """SQLAlchemy implementation of FeedbackRepository"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def create(self, feedback: Feedback) -> Feedback:
        """Create a new feedback"""
        feedback_model = FeedbackModel(
            session_id=feedback.session_id,
            student_id=feedback.student_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            created_at=feedback.created_at or datetime.now()
        )
        self.db.session.add(feedback_model)
        self.db.session.commit()
        return self._to_domain(feedback_model)
    
    def get_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """Get feedback by ID"""
        feedback_model = FeedbackModel.query.get(feedback_id)
        return self._to_domain(feedback_model) if feedback_model else None
    
    def get_by_session_id(self, session_id: int) -> List[Feedback]:
        """Get feedback by session ID"""
        feedbacks = FeedbackModel.query.filter_by(session_id=session_id).all()
        return [self._to_domain(feedback) for feedback in feedbacks]
    
    def get_by_student_id(self, student_id: int) -> List[Feedback]:
        """Get feedback by student ID"""
        feedbacks = FeedbackModel.query.filter_by(student_id=student_id).all()
        return [self._to_domain(feedback) for feedback in feedbacks]
    
    def update(self, feedback: Feedback) -> Feedback:
        """Update feedback"""
        feedback_model = FeedbackModel.query.get(feedback.feedback_id)
        if not feedback_model:
            raise ValueError(f"Feedback with ID {feedback.feedback_id} not found")
        
        feedback_model.rating = feedback.rating
        feedback_model.feedback_text = feedback.feedback_text
        
        self.db.session.commit()
        return self._to_domain(feedback_model)
    
    def delete(self, feedback_id: int) -> bool:
        """Delete feedback"""
        feedback_model = FeedbackModel.query.get(feedback_id)
        if feedback_model:
            self.db.session.delete(feedback_model)
            self.db.session.commit()
            return True
        return False
    
    def get_average_rating(self, session_id: Optional[int] = None) -> float:
        """Get average rating"""
        query = FeedbackModel.query
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        result = self.db.session.query(self.db.func.avg(FeedbackModel.rating)).scalar()
        return float(result) if result else 0.0
    
    def _to_domain(self, feedback_model: FeedbackModel) -> Feedback:
        """Convert SQLAlchemy model to domain entity"""
        return Feedback(
            feedback_id=feedback_model.feedback_id,
            session_id=feedback_model.session_id,
            student_id=feedback_model.student_id,
            rating=feedback_model.rating,
            feedback_text=feedback_model.feedback_text,
            created_at=feedback_model.created_at
        )


class SQLAlchemyTrainingDataRepository(TrainingDataRepository):
    """SQLAlchemy implementation of TrainingDataRepository"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def create(self, training_data: TrainingData) -> TrainingData:
        """Create new training data"""
        training_data_model = TrainingDataModel(
            admin_id=training_data.admin_id,
            input_text=training_data.input_text,
            output_text=training_data.output_text,
            language=training_data.language.value,
            category=training_data.category,
            added_at=training_data.added_at or datetime.now(),
            is_approved=training_data.is_approved
        )
        self.db.session.add(training_data_model)
        self.db.session.commit()
        return self._to_domain(training_data_model)
    
    def get_by_id(self, data_id: int) -> Optional[TrainingData]:
        """Get training data by ID"""
        training_data_model = TrainingDataModel.query.get(data_id)
        return self._to_domain(training_data_model) if training_data_model else None
    
    def get_approved_data(self) -> List[TrainingData]:
        """Get approved training data"""
        training_data = TrainingDataModel.query.filter_by(is_approved=True).all()
        return [self._to_domain(data) for data in training_data]
    
    def get_pending_data(self) -> List[TrainingData]:
        """Get pending training data"""
        training_data = TrainingDataModel.query.filter_by(is_approved=False).all()
        return [self._to_domain(data) for data in training_data]
    
    def update(self, training_data: TrainingData) -> TrainingData:
        """Update training data"""
        training_data_model = TrainingDataModel.query.get(training_data.data_id)
        if not training_data_model:
            raise ValueError(f"Training data with ID {training_data.data_id} not found")
        
        training_data_model.input_text = training_data.input_text
        training_data_model.output_text = training_data.output_text
        training_data_model.language = training_data.language.value
        training_data_model.category = training_data.category
        training_data_model.is_approved = training_data.is_approved
        
        self.db.session.commit()
        return self._to_domain(training_data_model)
    
    def delete(self, data_id: int) -> bool:
        """Delete training data"""
        training_data_model = TrainingDataModel.query.get(data_id)
        if training_data_model:
            self.db.session.delete(training_data_model)
            self.db.session.commit()
            return True
        return False
    
    def approve(self, data_id: int) -> bool:
        """Approve training data"""
        training_data_model = TrainingDataModel.query.get(data_id)
        if training_data_model:
            training_data_model.is_approved = True
            self.db.session.commit()
            return True
        return False
    
    def reject(self, data_id: int) -> bool:
        """Reject training data"""
        training_data_model = TrainingDataModel.query.get(data_id)
        if training_data_model:
            training_data_model.is_approved = False
            self.db.session.commit()
            return True
        return False
    
    def _to_domain(self, training_data_model: TrainingDataModel) -> TrainingData:
        """Convert SQLAlchemy model to domain entity"""
        return TrainingData(
            data_id=training_data_model.data_id,
            admin_id=training_data_model.admin_id,
            input_text=training_data_model.input_text,
            output_text=training_data_model.output_text,
            language=Language(training_data_model.language),
            category=training_data_model.category,
            added_at=training_data_model.added_at,
            is_approved=training_data_model.is_approved
        ) 