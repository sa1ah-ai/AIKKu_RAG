from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import User, Student, Admin, ChatSession, ChatMessage, Feedback, TrainingData


class UserRepository(ABC):
    """Repository interface for User operations"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Update user"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        pass
    
    @abstractmethod
    def list_all(self, limit: Optional[int] = None) -> List[User]:
        """List all users"""
        pass


class StudentRepository(ABC):
    """Repository interface for Student operations"""
    
    @abstractmethod
    def create(self, student: Student) -> Student:
        """Create a new student"""
        pass
    
    @abstractmethod
    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Get student by ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        """Get student by user ID"""
        pass
    
    @abstractmethod
    def update(self, student: Student) -> Student:
        """Update student"""
        pass
    
    @abstractmethod
    def delete(self, student_id: int) -> bool:
        """Delete student"""
        pass
    
    @abstractmethod
    def list_all(self, limit: Optional[int] = None) -> List[Student]:
        """List all students"""
        pass


class AdminRepository(ABC):
    """Repository interface for Admin operations"""
    
    @abstractmethod
    def create(self, admin: Admin) -> Admin:
        """Create a new admin"""
        pass
    
    @abstractmethod
    def get_by_id(self, admin_id: int) -> Optional[Admin]:
        """Get admin by ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Admin]:
        """Get admin by user ID"""
        pass
    
    @abstractmethod
    def update(self, admin: Admin) -> Admin:
        """Update admin"""
        pass
    
    @abstractmethod
    def delete(self, admin_id: int) -> bool:
        """Delete admin"""
        pass


class ChatSessionRepository(ABC):
    """Repository interface for ChatSession operations"""
    
    @abstractmethod
    def create(self, session: ChatSession) -> ChatSession:
        """Create a new chat session"""
        pass
    
    @abstractmethod
    def get_by_id(self, session_id: int) -> Optional[ChatSession]:
        """Get chat session by ID"""
        pass
    
    @abstractmethod
    def get_by_student_id(self, student_id: int) -> List[ChatSession]:
        """Get chat sessions by student ID"""
        pass
    
    @abstractmethod
    def update(self, session: ChatSession) -> ChatSession:
        """Update chat session"""
        pass
    
    @abstractmethod
    def delete(self, session_id: int) -> bool:
        """Delete chat session"""
        pass
    
    @abstractmethod
    def get_active_sessions(self, student_id: int) -> List[ChatSession]:
        """Get active chat sessions for a student"""
        pass


class ChatMessageRepository(ABC):
    """Repository interface for ChatMessage operations"""
    
    @abstractmethod
    def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new chat message"""
        pass
    
    @abstractmethod
    def get_by_session_id(self, session_id: int) -> List[ChatMessage]:
        """Get messages by session ID"""
        pass
    
    @abstractmethod
    def get_by_id(self, message_id: int) -> Optional[ChatMessage]:
        """Get message by ID"""
        pass
    
    @abstractmethod
    def update(self, message: ChatMessage) -> ChatMessage:
        """Update chat message"""
        pass
    
    @abstractmethod
    def delete(self, message_id: int) -> bool:
        """Delete chat message"""
        pass


class FeedbackRepository(ABC):
    """Repository interface for Feedback operations"""
    
    @abstractmethod
    def create(self, feedback: Feedback) -> Feedback:
        """Create a new feedback"""
        pass
    
    @abstractmethod
    def get_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """Get feedback by ID"""
        pass
    
    @abstractmethod
    def get_by_session_id(self, session_id: int) -> List[Feedback]:
        """Get feedback by session ID"""
        pass
    
    @abstractmethod
    def get_by_student_id(self, student_id: int) -> List[Feedback]:
        """Get feedback by student ID"""
        pass
    
    @abstractmethod
    def update(self, feedback: Feedback) -> Feedback:
        """Update feedback"""
        pass
    
    @abstractmethod
    def delete(self, feedback_id: int) -> bool:
        """Delete feedback"""
        pass
    
    @abstractmethod
    def get_average_rating(self, session_id: Optional[int] = None) -> float:
        """Get average rating"""
        pass


class TrainingDataRepository(ABC):
    """Repository interface for TrainingData operations"""
    
    @abstractmethod
    def create(self, training_data: TrainingData) -> TrainingData:
        """Create new training data"""
        pass
    
    @abstractmethod
    def get_by_id(self, data_id: int) -> Optional[TrainingData]:
        """Get training data by ID"""
        pass
    
    @abstractmethod
    def get_approved_data(self) -> List[TrainingData]:
        """Get approved training data"""
        pass
    
    @abstractmethod
    def get_pending_data(self) -> List[TrainingData]:
        """Get pending training data"""
        pass
    
    @abstractmethod
    def update(self, training_data: TrainingData) -> TrainingData:
        """Update training data"""
        pass
    
    @abstractmethod
    def delete(self, data_id: int) -> bool:
        """Delete training data"""
        pass
    
    @abstractmethod
    def approve(self, data_id: int) -> bool:
        """Approve training data"""
        pass
    
    @abstractmethod
    def reject(self, data_id: int) -> bool:
        """Reject training data"""
        pass 