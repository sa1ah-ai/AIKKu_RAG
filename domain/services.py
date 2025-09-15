from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .entities import (
    User, Student, Admin, ChatSession, ChatMessage, Feedback, 
    TrainingData, RAGQuery, RAGResponse, UserType, Language, 
    SenderType, AccountStatus
)
from .repositories import (
    UserRepository, StudentRepository, AdminRepository, 
    ChatSessionRepository, ChatMessageRepository, 
    FeedbackRepository, TrainingDataRepository
)


class AuthenticationService(ABC):
    """Service for authentication operations"""
    
    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        pass
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        pass
    
    @abstractmethod
    def reset_password(self, email: str) -> bool:
        """Reset user password"""
        pass


class UserManagementService(ABC):
    """Service for user management operations"""
    
    @abstractmethod
    def get_user_profile(self, user_id: int) -> Optional[User]:
        """Get user profile"""
        pass
    
    @abstractmethod
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[User]:
        """Update user profile"""
        pass
    
    @abstractmethod
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        pass
    
    @abstractmethod
    def activate_user(self, user_id: int) -> bool:
        """Activate user account"""
        pass


class ChatService(ABC):
    """Service for chat operations"""
    
    @abstractmethod
    def create_chat_session(self, student_id: int, title: str) -> ChatSession:
        """Create a new chat session"""
        pass
    
    @abstractmethod
    def send_message(self, session_id: int, message_text: str, sender_type: SenderType) -> ChatMessage:
        """Send a message in a chat session"""
        pass
    
    @abstractmethod
    def get_chat_history(self, session_id: int) -> List[ChatMessage]:
        """Get chat history for a session"""
        pass
    
    @abstractmethod
    def get_user_sessions(self, student_id: int) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: int, student_id: int) -> bool:
        """Delete a chat session"""
        pass
    
    @abstractmethod
    def rename_session(self, session_id: int, student_id: int, new_title: str) -> bool:
        """Rename a chat session"""
        pass


class RAGService(ABC):
    """Service for RAG operations"""
    
    @abstractmethod
    def process_query(self, query: RAGQuery) -> RAGResponse:
        """Process a RAG query and return response"""
        pass
    
    @abstractmethod
    def update_knowledge_base(self, training_data: List[TrainingData]) -> bool:
        """Update the knowledge base with new training data"""
        pass
    
    @abstractmethod
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        pass


class FeedbackService(ABC):
    """Service for feedback operations"""
    
    @abstractmethod
    def submit_feedback(self, session_id: int, student_id: int, rating: int, feedback_text: str) -> Feedback:
        """Submit feedback for a chat session"""
        pass
    
    @abstractmethod
    def get_session_feedback(self, session_id: int) -> List[Feedback]:
        """Get feedback for a specific session"""
        pass
    
    @abstractmethod
    def get_user_feedback(self, student_id: int) -> List[Feedback]:
        """Get feedback from a specific user"""
        pass
    
    @abstractmethod
    def get_feedback_analytics(self) -> Dict[str, Any]:
        """Get feedback analytics"""
        pass


class AdminService(ABC):
    """Service for admin operations"""
    
    @abstractmethod
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get admin dashboard data"""
        pass
    
    @abstractmethod
    def manage_student(self, student_id: int, action: str, data: Dict[str, Any]) -> bool:
        """Manage student (edit, delete, etc.)"""
        pass
    
    @abstractmethod
    def manage_training_data(self, data_id: int, action: str) -> bool:
        """Manage training data (approve, reject, delete)"""
        pass
    
    @abstractmethod
    def upload_training_file(self, file_data: bytes, filename: str) -> bool:
        """Upload training file"""
        pass
    
    @abstractmethod
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system analytics"""
        pass


class NotificationService(ABC):
    """Service for notification operations"""
    
    @abstractmethod
    def notify_user(self, user_id: int, message: str, notification_type: str) -> bool:
        """Send notification to user"""
        pass
    
    @abstractmethod
    def notify_admin(self, message: str, notification_type: str) -> bool:
        """Send notification to admin"""
        pass


class FileService(ABC):
    """Service for file operations"""
    
    @abstractmethod
    def upload_profile_picture(self, user_id: int, file_data: bytes, filename: str) -> str:
        """Upload profile picture"""
        pass
    
    @abstractmethod
    def upload_training_file(self, file_data: bytes, filename: str) -> str:
        """Upload training file"""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        pass 