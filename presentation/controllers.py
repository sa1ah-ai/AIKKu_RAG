import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from typing import Dict, Any, Optional
import logging

import config
from domain.entities import UserType, SenderType, Language
from domain.services import (
    AuthenticationService, UserManagementService, ChatService,
    RAGService, FeedbackService, AdminService, FileService
)
from application.container import get_container


class BaseController:
    """Base controller with common functionality"""
    
    def __init__(self):
        self.container = get_container()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_current_user_id(self) -> Optional[int]:
        """Get current user ID from session"""
        return session.get('user_id')
    
    def get_current_user_type(self) -> Optional[str]:
        """Get current user type from session"""
        return session.get('user_type')
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get_current_user_id() is not None
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.get_current_user_type() == UserType.ADMIN.value
    
    def is_student(self) -> bool:
        """Check if current user is student"""
        return self.get_current_user_type() == UserType.STUDENT.value
    
    def require_auth(self):
        """Decorator to require authentication"""
        if not self.is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
    
    def require_admin(self):
        """Decorator to require admin privileges"""
        if not self.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
    
    def require_student(self):
        """Decorator to require student privileges"""
        if not self.is_student():
            return jsonify({'error': 'Student privileges required'}), 403


class AuthController(BaseController):
    """Controller for authentication operations"""
    
    def __init__(self):
        super().__init__()
        self.auth_service: AuthenticationService = self.container.get_service('auth')
    
    def login(self) -> Dict[str, Any]:
        """Handle user login"""
        try:
            data = request.get_json() if request.is_json else request.form
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return {'success': False, 'message': 'Email and password are required'}
            
            user = self.auth_service.authenticate_user(email, password)
            if user:
                session['user_id'] = user.user_id
                session['user_name'] = user.username
                session['user_type'] = user.user_type.value
                print(f"User {user.username} logged in successfully")
                return {'success': True, 'message': 'Login successful'}
            else:
                return {'success': False, 'message': 'Invalid email or password'}
        
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return {'success': False, 'message': 'Login failed'}
    
    def signup(self) -> dict:
        """Handle user signup"""
        try:
            data = request.get_json() if request.is_json else request.form

            # البيانات المطلوبة
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return {'success': False, 'message': f'{field.capitalize()} is required.'}
            
            # أي حقول إضافية يمكن تمريرها مع الطلب
            user_data = {
                'username': data.get('username'),
                'email': data.get('email'),
                'password': data.get('password'),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'user_type': data.get('user_type', 'student'),
                'language_preference': data.get('language_preference', 'English'),
                'university_id': data.get('university_id', ''),
                'major': data.get('major', ''),
                'year_of_study': data.get('year_of_study', ''),
            }
            
            user = self.auth_service.create_user(user_data)
            
            # تسجيل الدخول تلقائيًا بعد النجاح (اختياري)
            session['user_id'] = user.user_id
            session['user_name'] = user.username
            session['user_type'] = user.user_type.value

            self.logger.info(f"User {user.username} registered successfully")
            return {'success': True, 'message': 'Signup successful'}

        except ValueError as ve:
            self.logger.warning(f"Signup value error: {ve}")
            return {'success': False, 'message': str(ve)}
        except Exception as e:
            self.logger.error(f"Signup error: {e}")
            return {'success': False, 'message': 'Signup failed'}
    
    def logout(self) -> Dict[str, Any]:
        """Handle user logout"""
        session.clear()
        return {'success': True, 'message': 'Logout successful'}
    
    def forgot_password(self) -> Dict[str, Any]:
        """Handle forgot password request"""
        try:
            data = request.get_json() if request.is_json else request.form
            email = data.get('email')
            
            if not email:
                return {'success': False, 'message': 'Email is required'}
            
            success = self.auth_service.reset_password(email)
            if success:
                return {'success': True, 'message': 'Password reset link sent'}
            else:
                return {'success': False, 'message': 'Email not found'}
        
        except Exception as e:
            self.logger.error(f"Forgot password error: {e}")
            return {'success': False, 'message': 'Password reset failed'}


class UserController(BaseController):
    """Controller for user management operations"""
    
    def __init__(self):
        super().__init__()
        self.user_service: UserManagementService = self.container.get_service('user_management')
        self.file_service: FileService = self.container.get_service('file')
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            user = self.user_service.get_user_profile(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            
            return {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_picture_path': user.profile_picture_path,
                'language_preference': user.language_preference.value
            }
        
        except Exception as e:
            self.logger.error(f"Get profile error: {e}")
            return {'error': 'Failed to get profile'}, 500
    
    def update_profile(self) -> Dict[str, Any]:
        """Update user profile"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            profile_data = {}
            
            # Handle form data
            if request.form:
                profile_data.update({
                    'first_name': request.form.get('first_name'),
                    'last_name': request.form.get('last_name'),
                    'email': request.form.get('email'),
                    'language_preference': request.form.get('language_preference')
                })
                
                # Handle file upload
                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file_data = file.read()
                        profile_data['profile_picture'] = file_data
            
            # Handle JSON data
            elif request.is_json:
                profile_data.update(request.get_json())
            
            user = self.user_service.update_user_profile(user_id, profile_data)
            if user:
                return {'success': True, 'message': 'Profile updated successfully'}
            else:
                return {'error': 'Failed to update profile'}, 400
        
        except Exception as e:
            self.logger.error(f"Update profile error: {e}")
            return {'error': 'Failed to update profile'}, 500


class ChatController(BaseController):
    """Controller for chat operations"""
    
    def __init__(self):
        super().__init__()
        self.chat_service: ChatService = self.container.get_service('chat')
        self.rag_service: RAGService = self.container.get_service('rag')
    
    def send_message(self) -> Dict[str, Any]:
        """Send a chat message"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            data = request.get_json() if request.is_json else request.form
            message = data.get('msg', '').strip()
            session_id = data.get('session_id')
            
            if not message:
                return {'error': 'Message is empty'}, 400
            
            # Get student ID (assuming user is student)
            # In a real app, you'd get this from the user service
            student_id = user_id  # Simplified for now
            
            # Create new session if needed
            if not session_id:
                from datetime import datetime
                title = f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                session = self.chat_service.create_chat_session(student_id, title)
                session_id = session.session_id
            
            # Process message
            result = self.chat_service.process_chat_message(session_id, message, student_id)
            # print("AI response:", result['ai_response'].message_text)
            
            return {
                'response': result['ai_response'].message_text or "لم يتم توليد إجابة.",
                'session_id': session_id
            }
        
        # except Exception as e:
        #     self.logger.error(f"Send message error: {e}")
        #     return {'error': 'Failed to send message'}, 500
        except Exception as e:
            import sys, traceback
            print("Exception in send_message:", e)
            traceback.print_exc(file=sys.stdout)
            self.logger.error(f"Send message error: {e}")
            return {'error': 'Failed to send message'}, 500
    
    def get_chat_sessions(self) -> Dict[str, Any]:
        """Get user's chat sessions"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            # Get student ID (assuming user is student)
            student_id = user_id  # Simplified for now
            
            sessions = self.chat_service.get_user_sessions(student_id)
            
            session_list = [
                {
                    'session_id': s.session_id,
                    'session_title': s.session_title or f'Chat {s.session_id}',
                    'created_at': s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else ''
                }
                for s in sorted(sessions, key=lambda x: x.created_at, reverse=True)
            ]
            
            return {'sessions': session_list}
        
        except Exception as e:
            self.logger.error(f"Get chat sessions error: {e}")
            return {'error': 'Failed to get chat sessions'}, 500
    
    def get_chat_messages(self, session_id: int) -> Dict[str, Any]:
        """Get messages for a chat session"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            messages = self.chat_service.get_chat_history(session_id)
            
            messages_list = [
                {
                    'sender_type': m.sender_type.value,
                    'message_text': m.message_text,
                    'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else ''
                }
                for m in sorted(messages, key=lambda x: x.created_at)
            ]
            
            return {'messages': messages_list}
        
        except Exception as e:
            self.logger.error(f"Get chat messages error: {e}")
            return {'error': 'Failed to get chat messages'}, 500
    
    def delete_session(self, session_id: int) -> Dict[str, Any]:
        """Delete a chat session"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            # Get student ID (assuming user is student)
            student_id = user_id  # Simplified for now
            
            success = self.chat_service.delete_session(session_id, student_id)
            if success:
                return {'success': True, 'session_id': session_id}
            else:
                return {'error': 'Session not found or access denied'}, 404
        
        except Exception as e:
            self.logger.error(f"Delete session error: {e}")
            return {'error': 'Failed to delete session'}, 500
    
    def rename_session(self, session_id: int) -> Dict[str, Any]:
        """Rename a chat session"""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            data = request.get_json()
            new_title = data.get('session_title', '').strip()
            
            if not new_title:
                return {'error': 'Title cannot be empty'}, 400
            
            # Get student ID (assuming user is student)
            student_id = user_id  # Simplified for now
            
            success = self.chat_service.rename_session(session_id, student_id, new_title)
            if success:
                return {'success': True, 'session_id': session_id, 'session_title': new_title}
            else:
                return {'error': 'Session not found or access denied'}, 404
        
        except Exception as e:
            self.logger.error(f"Rename session error: {e}")
            return {'error': 'Failed to rename session'}, 500


class AdminController(BaseController):
    """Controller for admin operations"""
    
    def __init__(self):
        super().__init__()
        self.admin_service: AdminService = self.container.get_service('admin')
        self.file_service: FileService = self.container.get_service('file')
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get admin dashboard data"""
        try:
            if not self.is_admin():
                return {'error': 'Admin privileges required'}, 403
            
            dashboard_data = self.admin_service.get_dashboard_data()
            return dashboard_data
        
        except Exception as e:
            self.logger.error(f"Get dashboard error: {e}")
            return {'error': 'Failed to get dashboard data'}, 500

    def get_dashboard_data(self) -> Dict[str, Any]:
        students = self.student_repo.list_all()
        training_data = self.training_data_repo.get_pending_data()
        try:
            folder = self.file_service.training_data_dir  # already set in FileServiceImpl
            all_files = sorted(os.listdir(folder))
            allowed = config.files.allowed_extensions  # {'pdf','md'}
            pdf_files = [f for f in all_files if f.lower().rsplit('.',1)[-1] in allowed]
        except Exception:
            pdf_files = []

        return {
            'total_students': len(students),
            'pending_training_data': len(training_data),
            'recent_students': students[:10] if students else [],
            'students': students,
            'pdf_files': pdf_files,
        }
    
    # def upload_training_file(self) -> Dict[str, Any]:
    #     """Upload training file"""
    #     try:
    #         if not self.is_admin():
    #             return {'error': 'Admin privileges required'}, 403
            
    #         if 'pdf_file' not in request.files:
    #             return {'error': 'No file part'}, 400
            
    #         file = request.files['pdf_file']
    #         if file.filename == '':
    #             return {'error': 'No selected file'}, 400
            
    #         if not file.filename.lower().endswith('.pdf'):
    #             return {'error': 'Invalid file type. Only PDF allowed.'}, 400
            
    #         file_data = file.read()
    #         success = self.admin_service.upload_training_file(file_data, file.filename)
            
    #         if success:
    #             return {'success': True, 'message': 'File uploaded successfully'}
    #         else:
    #             return {'error': 'Failed to upload file'}, 500
        
    #     except Exception as e:
    #         self.logger.error(f"Upload training file error: {e}")
    #         return {'error': 'Failed to upload file'}, 500

    def upload_training_file(self) -> Dict[str, Any]:
        try:
            if not self.is_admin():
                return {'error': 'Admin privileges required'}, 403

            file = request.files.get('training_file') or request.files.get('pdf_file')
            if not file or file.filename == '':
                return {'error': 'No selected file'}, 400

            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower()

            allowed = config.files.allowed_extensions  # ✅ correct source
            if ext not in allowed:
                return {'error': f"Invalid file type. Allowed: {', '.join(sorted(allowed))}"}, 400

            file_data = file.read()
            success = self.admin_service.upload_training_file(file_data, filename)
            return ({'success': True, 'message': 'File uploaded successfully'}
                    if success else ({'error': 'Failed to upload file'}, 500))
        except Exception as e:
            self.logger.error(f"Upload training file error: {e}")
            return {'error': 'Failed to upload file'}, 500

    
    # def manage_student(self, student_id: int) -> Dict[str, Any]:
    #     """Manage student (edit/delete)"""
    #     try:
    #         if not self.is_admin():
    #             return {'error': 'Admin privileges required'}, 403
            
    #         data = request.get_json()
    #         action = data.get('action')
            
    #         if action == 'edit':
    #             success = self.admin_service.manage_student(student_id, 'edit', data)
    #         elif action == 'delete':
    #             success = self.admin_service.manage_student(student_id, 'delete', {})
    #         else:
    #             return {'error': 'Invalid action'}, 400
            
    #         if success:
    #             return {'success': True, 'message': f'Student {action} successful'}
    #         else:
    #             return {'error': 'Failed to manage student'}, 400
        
    #     except Exception as e:
    #         self.logger.error(f"Manage student error: {e}")
    #         return {'error': 'Failed to manage student'}, 500

    # in AdminController.manage_student

    def manage_student(self, student_id: int) -> Dict[str, Any]:
        try:
            if not self.is_admin():
                return {'error': 'Admin privileges required'}, 403

            # accept form or JSON
            data = request.get_json(silent=True) or request.form.to_dict()

            action = data.get('action')
            # infer action from URL path if missing
            if not action:
                p = request.path or ''
                if '/edit_student/' in p:
                    action = 'edit'
                elif '/delete_student/' in p:
                    action = 'delete'

            if action == 'edit':
                success = self.admin_service.manage_student(student_id, 'edit', data)
            elif action == 'delete':
                success = self.admin_service.manage_student(student_id, 'delete', {})
            else:
                return {'error': 'Invalid action'}, 400

            if success:
                return {'success': True, 'message': f'Student {action} successful'}
            else:
                return {'error': 'Failed to manage student'}, 400

        except Exception as e:
            self.logger.error(f"Manage student error: {e}")
            return {'error': 'Failed to manage student'}, 500


# Remove the module-level controller instances and create a factory function
def create_controllers():
    """Factory function to create controller instances with proper dependency injection"""
    return {
        'auth': AuthController(),
        'user': UserController(),
        'chat': ChatController(),
        'admin': AdminController()
    } 