from typing import List, Optional, Dict, Any
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os
import logging

from domain.services import (
    AuthenticationService, UserManagementService, ChatService, 
    RAGService, FeedbackService, AdminService, NotificationService, FileService
)
from domain.entities import (
    User, Student, Admin, ChatSession, ChatMessage, Feedback, 
    TrainingData, RAGQuery, RAGResponse, UserType, Language, 
    SenderType, AccountStatus
)
from domain.repositories import (
    UserRepository, StudentRepository, AdminRepository, 
    ChatSessionRepository, ChatMessageRepository, 
    FeedbackRepository, TrainingDataRepository
)
from config import config


class AuthenticationServiceImpl(AuthenticationService):
    """Implementation of AuthenticationService"""
    
    def __init__(self, user_repo: UserRepository, student_repo: StudentRepository):
        self.user_repo = user_repo
        self.student_repo = student_repo
        self.serializer = URLSafeTimedSerializer(config.app.secret_key)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.user_repo.get_by_email(email)
        if user and check_password_hash(user.password_hash, password) and user.is_active():
            return user
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.user_repo.get_by_email(user_data['email']):
            raise ValueError("User with this email already exists")
        
        if self.user_repo.get_by_username(user_data['username']):
            raise ValueError("Username already taken")
        
        # Create user
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=generate_password_hash(user_data['password']),
            user_type=UserType(user_data.get('user_type', 'student')),
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            language_preference=Language(user_data.get('language_preference', 'English'))
        )
        
        created_user = self.user_repo.create(user)
        
        # If student, create student record
        if created_user.is_student():
            student = Student(
                student_id=created_user.user_id,
                user=created_user,
                university_id=user_data.get('university_id', ''),
                major=user_data.get('major'),
                year_of_study=user_data.get('year_of_study')
            )
            self.student_repo.create(student)
        
        return created_user
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.user_repo.get_by_id(user_id)
        if not user or not check_password_hash(user.password_hash, old_password):
            return False
        
        user.password_hash = generate_password_hash(new_password)
        self.user_repo.update(user)
        return True
    
    def reset_password(self, email: str) -> bool:
        """Reset user password"""
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        
        # Generate reset token
        token = self.serializer.dumps(user.email, salt='password-reset-salt')
        # In a real application, send email with reset link
        # For now, just log it
        logging.info(f"Password reset token for {email}: {token}")
        return True


class UserManagementServiceImpl(UserManagementService):
    """Implementation of UserManagementService"""
    
    def __init__(self, user_repo: UserRepository, file_service: FileService):
        self.user_repo = user_repo
        self.file_service = file_service
    
    def get_user_profile(self, user_id: int) -> Optional[User]:
        """Get user profile"""
        return self.user_repo.get_by_id(user_id)
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[User]:
        """Update user profile"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # Update basic fields
        if 'first_name' in profile_data:
            user.first_name = profile_data['first_name']
        if 'last_name' in profile_data:
            user.last_name = profile_data['last_name']
        if 'email' in profile_data:
            user.email = profile_data['email']
        if 'language_preference' in profile_data:
            user.language_preference = Language(profile_data['language_preference'])
        
        # Handle profile picture upload
        if 'profile_picture' in profile_data:
            file_data = profile_data['profile_picture']
            filename = f"profile_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            file_path = self.file_service.upload_profile_picture(user_id, file_data, filename)
            user.profile_picture_path = file_path
        
        return self.user_repo.update(user)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        user.account_status = AccountStatus.SUSPENDED
        self.user_repo.update(user)
        return True
    
    def activate_user(self, user_id: int) -> bool:
        """Activate user account"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        user.account_status = AccountStatus.ACTIVE
        self.user_repo.update(user)
        return True


class ChatServiceImpl(ChatService):
    """Implementation of ChatService"""
    
    def __init__(self, session_repo: ChatSessionRepository, 
                 message_repo: ChatMessageRepository,
                 rag_service: RAGService):
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.rag_service = rag_service
    
    def create_chat_session(self, student_id: int, title: str) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            student_id=student_id,
            session_title=title,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        return self.session_repo.create(session)
    
    def send_message(self, session_id: int, message_text: str, sender_type: SenderType) -> ChatMessage:
        """Send a message in a chat session"""
        message = ChatMessage(
            session_id=session_id,
            sender_type=sender_type,
            message_text=message_text,
            is_arabic= True,  # TODO: Add language detection
            created_at=datetime.now()
        )
        # print("Message is arabic?:", message.is_arabic)
        created_message = self.message_repo.create(message)
        
        # Update session last activity
        session = self.session_repo.get_by_id(session_id)
        if session:
            session.last_activity = datetime.now()
            self.session_repo.update(session)
        
        return created_message
    
    def get_chat_history(self, session_id: int) -> List[ChatMessage]:
        """Get chat history for a session"""
        return self.message_repo.get_by_session_id(session_id)
    
    def get_user_sessions(self, student_id: int) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        return self.session_repo.get_by_student_id(student_id)
    
    def delete_session(self, session_id: int, student_id: int) -> bool:
        """Delete a chat session"""
        session = self.session_repo.get_by_id(session_id)
        if not session or session.student_id != student_id:
            return False
        
        return self.session_repo.delete(session_id)
    
    def rename_session(self, session_id: int, student_id: int, new_title: str) -> bool:
        """Rename a chat session"""
        session = self.session_repo.get_by_id(session_id)
        if not session or session.student_id != student_id:
            return False
        
        session.session_title = new_title
        self.session_repo.update(session)
        return True
    
    def process_chat_message(self, session_id: int, message_text: str, student_id: int) -> Dict[str, Any]:
        """Process a chat message and generate AI response"""
        # Save user message
        # print("User message:", message_text)
        user_message = self.send_message(session_id, message_text, SenderType.STUDENT)
        # print("User message saved:", user_message.message_text)
        
        # Generate AI response
        query = RAGQuery(
            query=message_text,
            top_k=config.ai.top_k,
            context_window=config.ai.context_window
        )
        
        rag_response = self.rag_service.process_query(query)
        # print("RAG response:", rag_response.answer)
        
        # Save AI response
        ai_message = self.send_message(session_id, rag_response.answer, SenderType.SYSTEM)
        
        return {
            'user_message': user_message,
            'ai_response': ai_message,
            'session_id': session_id
        }


class RAGServiceImpl(RAGService):
    """Implementation of RAGService"""
    
    def __init__(self, rag_system):
        self.rag_system = rag_system
    
    def process_query(self, query: RAGQuery) -> RAGResponse:
        """Process a RAG query and return response"""
        return self.rag_system.process_query(query)
    
    def update_knowledge_base(self, training_data: List[TrainingData]) -> bool:
        """Update the knowledge base with new training data"""
        # TODO: Implement knowledge base update logic
        # This would involve re-chunking, re-embedding, and updating the retrieval system
        return True
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        return {
            'model_loaded': self.rag_system.llm_model is not None,
            'embedding_model_loaded': self.rag_system.embedding_model is not None,
            'tokenizer_loaded': self.rag_system.tokenizer is not None
        }


class FeedbackServiceImpl(FeedbackService):
    """Implementation of FeedbackService"""
    
    def __init__(self, feedback_repo: FeedbackRepository):
        self.feedback_repo = feedback_repo
    
    def submit_feedback(self, session_id: int, student_id: int, rating: int, feedback_text: str) -> Feedback:
        """Submit feedback for a chat session"""
        feedback = Feedback(
            session_id=session_id,
            student_id=student_id,
            rating=rating,
            feedback_text=feedback_text,
            created_at=datetime.now()
        )
        return self.feedback_repo.create(feedback)
    
    def get_session_feedback(self, session_id: int) -> List[Feedback]:
        """Get feedback for a specific session"""
        return self.feedback_repo.get_by_session_id(session_id)
    
    def get_user_feedback(self, student_id: int) -> List[Feedback]:
        """Get feedback from a specific user"""
        return self.feedback_repo.get_by_student_id(student_id)
    
    def get_feedback_analytics(self) -> Dict[str, Any]:
        """Get feedback analytics"""
        # TODO: Implement analytics logic
        return {
            'total_feedback': 0,
            'average_rating': 0.0,
            'positive_feedback_count': 0,
            'negative_feedback_count': 0
        }


class AdminServiceImpl(AdminService):
    """Implementation of AdminService"""
    
    def __init__(self, user_repo: UserRepository, student_repo: StudentRepository,
                 training_data_repo: TrainingDataRepository, file_service: FileService):
        self.user_repo = user_repo
        self.student_repo = student_repo
        self.training_data_repo = training_data_repo
        self.file_service = file_service
    
    # def get_dashboard_data(self) -> Dict[str, Any]:
    #     """Get admin dashboard data"""
    #     students = self.student_repo.list_all()
    #     training_data = self.training_data_repo.get_pending_data()
    #     pdf_dir = config.files.training_data_folder  # usually 'training_data'

    #     try:
    #         pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    #     except Exception as e:
    #         pdf_files = []
        
    #     # return {
    #     #     'total_students': len(students),
    #     #     'pending_training_data': len(training_data),
    #     #     'recent_students': students[:10] if students else []
    #     # }
    #     return {
    #         'students': students[:10] if students else [],
    #         'pdf_files': pdf_files,
    #     }
    # def get_dashboard_data(self):
    #     students = self.student_repo.list_all()
    #     pdf_dir = config.files.training_data_folder
    #     try:
    #         pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(('.pdf', '.md'))]
    #     except Exception:
    #         pdf_files = []
    #     return {
    #         'students': students,
    #         'pdf_files': pdf_files,
    #     }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        students = self.student_repo.list_all()
        training_data = self.training_data_repo.get_pending_data()
        # list uploaded files for display
        try:
            folder = self.file_service.training_data_dir  # path from FileServiceImpl
            pdf_files = sorted(os.listdir(folder))
        except Exception:
            pdf_files = []

        return {
            'total_students': len(students),
            'pending_training_data': len(training_data),
            'recent_students': students[:10] if students else [],
            # needed by template:
            'students': students,
            'pdf_files': pdf_files,
        }

    # def manage_student(self, student_id: int, action: str, data: Dict[str, Any]) -> bool:
    #     """Manage student (edit, delete, etc.)"""
    #     if action == 'edit':
    #         student = self.student_repo.get_by_id(student_id)
    #         if not student:
    #             return False
            
    #         # Update student data
    #         if 'university_id' in data:
    #             student.university_id = data['university_id']
    #         if 'major' in data:
    #             student.major = data['major']
    #         if 'year_of_study' in data:
    #             student.year_of_study = data['year_of_study']
            
    #         self.student_repo.update(student)
    #         return True
        
    #     elif action == 'delete':
    #         return self.student_repo.delete(student_id)
        
    #     return False
    
    def manage_student(self, student_id: int, action: str, data: Dict[str, Any]) -> bool:
        if action == 'edit':
            student = self.student_repo.get_by_id(student_id)
            if not student:
                return False

            # update student fields
            if 'university_id' in data:
                student.university_id = data['university_id']
            if 'major' in data:
                student.major = data['major']
            if 'year_of_study' in data and str(data['year_of_study']).strip() != '':
                try:
                    student.year_of_study = int(data['year_of_study'])
                except ValueError:
                    pass
            self.student_repo.update(student)

            # also update related user (username/email) if provided
            user_changed = False
            if student.user:
                if 'username' in data and data['username'].strip():
                    student.user.username = data['username'].strip()
                    user_changed = True
                if 'email' in data and data['email'].strip():
                    student.user.email = data['email'].strip()
                    user_changed = True
                if user_changed:
                    self.user_repo.update(student.user)

            return True

            # delete
        elif action == 'delete':
            return self.student_repo.delete(student_id)

        return False
    
    def manage_training_data(self, data_id: int, action: str) -> bool:
        """Manage training data (approve, reject, delete)"""
        if action == 'approve':
            return self.training_data_repo.approve(data_id)
        elif action == 'reject':
            return self.training_data_repo.reject(data_id)
        elif action == 'delete':
            return self.training_data_repo.delete(data_id)
        
        return False
    
    # def upload_training_file(self, file_data: bytes, filename: str) -> bool:
    #     """Upload training file"""
    #     try:
    #         file_path = self.file_service.upload_training_file(file_data, filename)
    #         return True
    #     except Exception as e:
    #         logging.error(f"Error uploading training file: {e}")
    #         return False

    def upload_training_file(self, file_data: bytes, filename: str) -> bool:
        try:
            _ = self.file_service.upload_training_file(file_data, filename)
            return True
        except Exception as e:
            logging.error(f"Error uploading training file: {e}")
            return False
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system analytics"""
        # TODO: Implement comprehensive analytics
        return {
            'total_users': 0,
            'active_sessions': 0,
            'total_messages': 0,
            'system_uptime': 0
        }


class NotificationServiceImpl(NotificationService):
    """Implementation of NotificationService"""
    
    def notify_user(self, user_id: int, message: str, notification_type: str) -> bool:
        """Send notification to user"""
        # TODO: Implement actual notification logic (email, push, etc.)
        logging.info(f"Notification to user {user_id}: {message} ({notification_type})")
        return True
    
    def notify_admin(self, message: str, notification_type: str) -> bool:
        """Send notification to admin"""
        # TODO: Implement actual notification logic
        logging.info(f"Admin notification: {message} ({notification_type})")
        return True


class FileServiceImpl(FileService):
    """Implementation of FileService"""
    
    def __init__(self):
        self.profile_pics_dir = config.files.profile_pics_folder
        self.training_data_dir = config.files.training_data_folder
        
        # Create directories if they don't exist
        os.makedirs(self.profile_pics_dir, exist_ok=True)
        os.makedirs(self.training_data_dir, exist_ok=True)
    
    def upload_profile_picture(self, user_id: int, file_data: bytes, filename: str) -> str:
        """Upload profile picture"""
        file_path = os.path.join(self.profile_pics_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return f'profile_pics/{filename}'
    
    def upload_training_file(self, file_data: bytes, filename: str) -> str:
        """Upload training file"""
        file_path = os.path.join(self.training_data_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return f'training_data/{filename}'
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'exists': True
        } 