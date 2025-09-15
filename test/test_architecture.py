#!/usr/bin/env python3
"""
Test file to demonstrate the new Clean Architecture implementation
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Import domain entities
from domain.entities import (
    User, Student, ChatSession, ChatMessage, RAGQuery, RAGResponse,
    UserType, Language, SenderType, AccountStatus
)

# Import domain services
from domain.services import ChatService, RAGService

# Import application services
from application.services import ChatServiceImpl, RAGServiceImpl

# Import repositories
from domain.repositories import ChatSessionRepository, ChatMessageRepository


class MockChatSessionRepository(ChatSessionRepository):
    """Mock implementation of ChatSessionRepository for testing"""
    
    def __init__(self):
        self.sessions = {}
        self.next_id = 1
    
    def create(self, session: ChatSession) -> ChatSession:
        session.session_id = self.next_id
        self.sessions[session.session_id] = session
        self.next_id += 1
        return session
    
    def get_by_id(self, session_id: int):
        return self.sessions.get(session_id)
    
    def get_by_student_id(self, student_id: int):
        return [s for s in self.sessions.values() if s.student_id == student_id]
    
    def update(self, session: ChatSession) -> ChatSession:
        if session.session_id in self.sessions:
            self.sessions[session.session_id] = session
        return session
    
    def delete(self, session_id: int) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_active_sessions(self, student_id: int):
        return [s for s in self.sessions.values() 
                if s.student_id == student_id and s.is_active()]


class MockChatMessageRepository(ChatMessageRepository):
    """Mock implementation of ChatMessageRepository for testing"""
    
    def __init__(self):
        self.messages = {}
        self.next_id = 1
    
    def create(self, message: ChatMessage) -> ChatMessage:
        message.message_id = self.next_id
        self.messages[message.message_id] = message
        self.next_id += 1
        return message
    
    def get_by_session_id(self, session_id: int):
        return [m for m in self.messages.values() if m.session_id == session_id]
    
    def get_by_id(self, message_id: int):
        return self.messages.get(message_id)
    
    def update(self, message: ChatMessage) -> ChatMessage:
        if message.message_id in self.messages:
            self.messages[message.message_id] = message
        return message
    
    def delete(self, message_id: int) -> bool:
        if message_id in self.messages:
            del self.messages[message_id]
            return True
        return False


class MockRAGService(RAGService):
    """Mock implementation of RAGService for testing"""
    
    def process_query(self, query: RAGQuery) -> RAGResponse:
        # Mock response
        return RAGResponse(
            answer=f"Mock response to: {query.query}",
            sources=[{"chunk_text": "Mock source", "section_title": "Test"}],
            confidence=0.8,
            processing_time=0.1
        )
    
    def update_knowledge_base(self, training_data):
        return True
    
    def get_model_status(self):
        return {"status": "mock", "model_loaded": True}


class TestCleanArchitecture(unittest.TestCase):
    """Test cases for the Clean Architecture implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock repositories
        self.session_repo = MockChatSessionRepository()
        self.message_repo = MockChatMessageRepository()
        
        # Create mock RAG service
        self.rag_service = MockRAGService()
        
        # Create chat service with dependencies
        self.chat_service = ChatServiceImpl(
            self.session_repo,
            self.message_repo,
            self.rag_service
        )
        
        # Create test user and student
        self.test_user = User(
            user_id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            user_type=UserType.STUDENT,
            first_name="Test",
            last_name="User",
            language_preference=Language.ENGLISH,
            account_status=AccountStatus.ACTIVE
        )
        
        self.test_student = Student(
            student_id=1,
            user=self.test_user,
            university_id="U123",
            major="Computer Science",
            year_of_study=3
        )
    
    def test_create_chat_session(self):
        """Test creating a new chat session"""
        # Arrange
        student_id = 1
        title = "Test Chat Session"
        
        # Act
        session = self.chat_service.create_chat_session(student_id, title)
        
        # Assert
        self.assertIsNotNone(session)
        self.assertEqual(session.student_id, student_id)
        self.assertEqual(session.session_title, title)
        self.assertTrue(session.is_active())
        self.assertIsNotNone(session.session_id)
    
    def test_send_message(self):
        """Test sending a message in a chat session"""
        # Arrange
        session = self.chat_service.create_chat_session(1, "Test Session")
        message_text = "Hello, this is a test message"
        sender_type = SenderType.STUDENT
        
        # Act
        message = self.chat_service.send_message(
            session.session_id, 
            message_text, 
            sender_type
        )
        
        # Assert
        self.assertIsNotNone(message)
        self.assertEqual(message.message_text, message_text)
        self.assertEqual(message.sender_type, sender_type)
        self.assertEqual(message.session_id, session.session_id)
        self.assertIsNotNone(message.message_id)
    
    def test_get_chat_history(self):
        """Test retrieving chat history"""
        # Arrange
        session = self.chat_service.create_chat_session(1, "Test Session")
        self.chat_service.send_message(session.session_id, "Message 1", SenderType.STUDENT)
        self.chat_service.send_message(session.session_id, "Message 2", SenderType.SYSTEM)
        
        # Act
        messages = self.chat_service.get_chat_history(session.session_id)
        
        # Assert
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].message_text, "Message 1")
        self.assertEqual(messages[1].message_text, "Message 2")
    
    def test_process_chat_message(self):
        """Test processing a chat message with RAG response"""
        # Arrange
        session = self.chat_service.create_chat_session(1, "Test Session")
        message_text = "What is machine learning?"
        student_id = 1
        
        # Act
        result = self.chat_service.process_chat_message(
            session.session_id, 
            message_text, 
            student_id
        )
        
        # Assert
        self.assertIn('user_message', result)
        self.assertIn('ai_response', result)
        self.assertIn('session_id', result)
        
        self.assertEqual(result['user_message'].message_text, message_text)
        self.assertEqual(result['user_message'].sender_type, SenderType.STUDENT)
        self.assertEqual(result['ai_response'].sender_type, SenderType.SYSTEM)
        self.assertIn("Mock response to:", result['ai_response'].message_text)
    
    def test_delete_session(self):
        """Test deleting a chat session"""
        # Arrange
        session = self.chat_service.create_chat_session(1, "Test Session")
        session_id = session.session_id
        
        # Act
        success = self.chat_service.delete_session(session_id, 1)
        
        # Assert
        self.assertTrue(success)
        
        # Verify session is deleted
        retrieved_session = self.session_repo.get_by_id(session_id)
        self.assertIsNone(retrieved_session)
    
    def test_rename_session(self):
        """Test renaming a chat session"""
        # Arrange
        session = self.chat_service.create_chat_session(1, "Original Title")
        new_title = "New Title"
        
        # Act
        success = self.chat_service.rename_session(
            session.session_id, 
            1, 
            new_title
        )
        
        # Assert
        self.assertTrue(success)
        
        # Verify title is updated
        updated_session = self.session_repo.get_by_id(session.session_id)
        self.assertEqual(updated_session.session_title, new_title)
    
    def test_rag_service_mock(self):
        """Test RAG service mock functionality"""
        # Arrange
        query = RAGQuery(
            query="What is artificial intelligence?",
            top_k=3,
            context_window=0,
            language=Language.ENGLISH
        )
        
        # Act
        response = self.rag_service.process_query(query)
        
        # Assert
        self.assertIsInstance(response, RAGResponse)
        self.assertIn("Mock response to:", response.answer)
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(response.confidence, 0.8)
        self.assertGreater(response.processing_time, 0)


class TestDomainEntities(unittest.TestCase):
    """Test cases for domain entities"""
    
    def test_user_entity(self):
        """Test User entity functionality"""
        # Arrange & Act
        user = User(
            user_id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            user_type=UserType.STUDENT,
            first_name="Test",
            last_name="User"
        )
        
        # Assert
        self.assertTrue(user.is_active())
        self.assertTrue(user.is_student())
        self.assertFalse(user.is_admin())
        self.assertEqual(user.get_full_name(), "Test User")
    
    def test_chat_session_entity(self):
        """Test ChatSession entity functionality"""
        # Arrange
        session = ChatSession(
            session_id=1,
            student_id=1,
            session_title="Test Session",
            created_at=datetime.now()
        )
        
        # Act & Assert
        self.assertTrue(session.is_active())
        self.assertEqual(session.get_messages_count(), 0)
        self.assertIsNone(session.get_last_message())
        
        # Test adding messages
        message = ChatMessage(
            session_id=1,
            sender_type=SenderType.STUDENT,
            message_text="Test message"
        )
        
        session.add_message(message)
        
        self.assertEqual(session.get_messages_count(), 1)
        self.assertEqual(session.get_last_message(), message)
    
    def test_rag_query_entity(self):
        """Test RAGQuery entity functionality"""
        # Arrange
        query = RAGQuery(
            query="Test query",
            top_k=5,
            context_window=1,
            language=Language.ARABIC
        )
        
        # Act & Assert
        self.assertTrue(query.is_arabic())
        self.assertEqual(query.top_k, 5)
        self.assertEqual(query.context_window, 1)


def run_architecture_demo():
    """Run a demonstration of the Clean Architecture"""
    print("🚀 AIKKu RAG - Clean Architecture Demo")
    print("=" * 50)
    
    # Create test instance
    test = TestCleanArchitecture()
    test.setUp()
    
    print("\n📝 Testing Chat Session Creation:")
    session = test.chat_service.create_chat_session(1, "Demo Session")
    print(f"✅ Created session: {session.session_title} (ID: {session.session_id})")
    
    print("\n💬 Testing Message Sending:")
    message = test.chat_service.send_message(
        session.session_id, 
        "Hello, how does machine learning work?", 
        SenderType.STUDENT
    )
    print(f"✅ Sent message: {message.message_text}")
    
    print("\n🤖 Testing RAG Processing:")
    result = test.chat_service.process_chat_message(
        session.session_id, 
        "What is artificial intelligence?", 
        1
    )
    print(f"✅ AI Response: {result['ai_response'].message_text}")
    
    print("\n📊 Testing Chat History:")
    messages = test.chat_service.get_chat_history(session.session_id)
    print(f"✅ Retrieved {len(messages)} messages from session")
    
    print("\n🎯 Testing Session Management:")
    success = test.chat_service.rename_session(session.session_id, 1, "Updated Session")
    print(f"✅ Session renamed: {success}")
    
    print("\n🏗️ Architecture Benefits Demonstrated:")
    print("✅ Separation of Concerns: Each layer has specific responsibilities")
    print("✅ Dependency Injection: Services receive dependencies through constructor")
    print("✅ Testability: Easy to mock dependencies for testing")
    print("✅ Maintainability: Changes are localized to specific layers")
    print("✅ Scalability: Easy to add new features without affecting existing code")
    
    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    # Run the demo
    run_architecture_demo()
    
    # Run unit tests
    print("\n🧪 Running Unit Tests:")
    unittest.main(argv=[''], exit=False, verbosity=2) 