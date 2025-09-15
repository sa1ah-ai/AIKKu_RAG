from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class UserType(Enum):
    STUDENT = "student"
    ADMIN = "admin"


class Language(Enum):
    ENGLISH = "English"
    ARABIC = "Arabic"


class AccountStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SenderType(Enum):
    STUDENT = "student"
    SYSTEM = "system"


@dataclass
class User:
    """Domain entity for User"""
    user_id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    user_type: UserType = UserType.STUDENT
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture_path: Optional[str] = None
    language_preference: Language = Language.ENGLISH
    account_status: AccountStatus = AccountStatus.ACTIVE
    created_at: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.account_status == AccountStatus.ACTIVE
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.user_type == UserType.ADMIN
    
    def is_student(self) -> bool:
        """Check if user is student"""
        return self.user_type == UserType.STUDENT
    
    def get_full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username


@dataclass
class Student:
    """Domain entity for Student"""
    student_id: int
    user: User
    university_id: str
    major: Optional[str] = None
    year_of_study: Optional[int] = None
    chat_sessions: List['ChatSession'] = field(default_factory=list)
    
    def add_chat_session(self, session: 'ChatSession') -> None:
        """Add a new chat session"""
        self.chat_sessions.append(session)
    
    def get_active_sessions(self) -> List['ChatSession']:
        """Get active chat sessions"""
        return [session for session in self.chat_sessions if session.is_active()]


@dataclass
class Admin:
    """Domain entity for Admin"""
    admin_id: int
    user: User
    department: Optional[str] = None
    position: Optional[str] = None
    access_level: int = 1


@dataclass
class ChatSession:
    """Domain entity for Chat Session"""
    session_id: Optional[int] = None
    student_id: int = 0
    session_title: str = ""
    language_used: Language = Language.ENGLISH
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    messages: List['ChatMessage'] = field(default_factory=list)
    is_deleted: bool = False
    
    def is_active(self) -> bool:
        """Check if session is active"""
        return not self.is_deleted
    
    def add_message(self, message: 'ChatMessage') -> None:
        """Add a message to the session"""
        self.messages.append(message)
        self.last_activity = datetime.now()
    
    def get_messages_count(self) -> int:
        """Get total messages count"""
        return len(self.messages)
    
    def get_last_message(self) -> Optional['ChatMessage']:
        """Get the last message in the session"""
        return self.messages[-1] if self.messages else None


@dataclass
class ChatMessage:
    """Domain entity for Chat Message"""
    message_id: Optional[int] = None
    session_id: int = 0
    sender_type: SenderType = SenderType.STUDENT
    message_text: str = ""
    is_arabic: bool = True
    created_at: Optional[datetime] = None
    
    def is_from_student(self) -> bool:
        """Check if message is from student"""
        return self.sender_type == SenderType.STUDENT
    
    def is_from_system(self) -> bool:
        """Check if message is from system"""
        return self.sender_type == SenderType.SYSTEM


@dataclass
class Feedback:
    """Domain entity for Feedback"""
    feedback_id: Optional[int] = None
    session_id: int = 0
    student_id: int = 0
    rating: int = 0
    feedback_text: str = ""
    created_at: Optional[datetime] = None
    
    def is_positive(self) -> bool:
        """Check if feedback is positive (rating >= 4)"""
        return self.rating >= 4
    
    def is_negative(self) -> bool:
        """Check if feedback is negative (rating <= 2)"""
        return self.rating <= 2


@dataclass
class TrainingData:
    """Domain entity for Training Data"""
    data_id: Optional[int] = None
    admin_id: Optional[int] = None
    input_text: str = ""
    output_text: str = ""
    language: Language = Language.ARABIC
    category: Optional[str] = None
    added_at: Optional[datetime] = None
    is_approved: bool = False
    
    def approve(self) -> None:
        """Approve the training data"""
        self.is_approved = True
    
    def reject(self) -> None:
        """Reject the training data"""
        self.is_approved = False


@dataclass
class RAGQuery:
    """Domain entity for RAG Query"""
    query: str
    top_k: int = 3
    context_window: int = 0
    language: Language = Language.ARABIC
    
    def is_arabic(self) -> bool:
        """Check if query is in Arabic"""
        return self.language == Language.ARABIC


@dataclass
class RAGResponse:
    """Domain entity for RAG Response"""
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    processing_time: float = 0.0
    
    def add_source(self, source: Dict[str, Any]) -> None:
        """Add a source to the response"""
        self.sources.append(source)
    
    def get_sources_count(self) -> int:
        """Get number of sources"""
        return len(self.sources) 