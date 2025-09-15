from typing import Dict, Any
from flask_sqlalchemy import SQLAlchemy
from infrastructure.database.repositories import (
    SQLAlchemyUserRepository, SQLAlchemyStudentRepository, 
    SQLAlchemyChatSessionRepository, SQLAlchemyChatMessageRepository,
    SQLAlchemyFeedbackRepository, SQLAlchemyTrainingDataRepository
)
from infrastructure.ai.factories import get_ai_factory, get_rag_factory
from application.services import (
    AuthenticationServiceImpl, UserManagementServiceImpl, ChatServiceImpl,
    RAGServiceImpl, FeedbackServiceImpl, AdminServiceImpl,
    NotificationServiceImpl, FileServiceImpl
)
from ai.utils.chunking import MDChunker
from ai.utils.embedding import Embedder
from ai.utils.retrieval import Retriever
from config import config


class DependencyContainer:
    """Dependency injection container"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self._repositories = {}
        self._services = {}
        self._ai_components = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all dependencies"""
        if self._initialized:
            return
        
        # Initialize repositories
        self._initialize_repositories()
        
        # Initialize AI components
        self._initialize_ai_components()
        
        # Initialize services
        self._initialize_services()
        
        self._initialized = True
    
    def _initialize_repositories(self):
        """Initialize repository instances"""
        self._repositories['user'] = SQLAlchemyUserRepository(self.db)
        self._repositories['student'] = SQLAlchemyStudentRepository(
            self.db, self._repositories['user']
        )
        self._repositories['chat_session'] = SQLAlchemyChatSessionRepository(self.db)
        self._repositories['chat_message'] = SQLAlchemyChatMessageRepository(self.db)
        self._repositories['feedback'] = SQLAlchemyFeedbackRepository(self.db)
        self._repositories['training_data'] = SQLAlchemyTrainingDataRepository(self.db)
    
    def _initialize_ai_components(self):
        """Initialize AI components"""
        # Get AI factory
        ai_factory = get_ai_factory()
        rag_factory = get_rag_factory()
        
        # Initialize chunker
        self._ai_components['chunker'] = MDChunker()
        
        # Initialize embedder
        self._ai_components['embedder'] = Embedder()
        
        # Load embeddings
        embeddings, metadata = self._ai_components['embedder'].load_embeddings(
            config.files.embeddings_folder
        )
        
        # Initialize retriever
        retrieval_model = ai_factory.create_embedding_model(config.ai.embedding_model)
        self._ai_components['retriever'] = Retriever(embeddings, metadata, retrieval_model)
        
        # Initialize RAG system
        rag_config = {
            'model_id': config.ai.model_id,
            'embedding_model': config.ai.embedding_model,
            'max_tokens': config.ai.max_tokens,
            'top_k': config.ai.top_k,
            'context_window': config.ai.context_window,
            'max_context_tokens': config.ai.max_context_tokens
        }
        
        self._ai_components['rag_system'] = rag_factory.create_rag_system(rag_config)
        
        # Set dependencies for RAG system
        self._ai_components['rag_system'].retriever = self._ai_components['retriever']
        self._ai_components['rag_system'].chunker = self._ai_components['chunker']
    
    def _initialize_services(self):
        """Initialize service instances"""
        # Initialize file service first (no dependencies)
        self._services['file'] = FileServiceImpl()
        
        # Initialize notification service
        self._services['notification'] = NotificationServiceImpl()
        
        # Initialize repositories-dependent services
        self._services['auth'] = AuthenticationServiceImpl(
            self._repositories['user'],
            self._repositories['student']
        )
        
        self._services['user_management'] = UserManagementServiceImpl(
            self._repositories['user'],
            self._services['file']
        )
        
        self._services['rag'] = RAGServiceImpl(
            self._ai_components['rag_system']
        )
        
        self._services['chat'] = ChatServiceImpl(
            self._repositories['chat_session'],
            self._repositories['chat_message'],
            self._services['rag']
        )
        
        self._services['feedback'] = FeedbackServiceImpl(
            self._repositories['feedback']
        )
        
        self._services['admin'] = AdminServiceImpl(
            self._repositories['user'],
            self._repositories['student'],
            self._repositories['training_data'],
            self._services['file']
        )
    
    def get_repository(self, name: str):
        """Get repository by name"""
        if not self._initialized:
            self.initialize()
        return self._repositories.get(name)
    
    def get_service(self, name: str):
        """Get service by name"""
        if not self._initialized:
            self.initialize()
        return self._services.get(name)
    
    def get_ai_component(self, name: str):
        """Get AI component by name"""
        if not self._initialized:
            self.initialize()
        return self._ai_components.get(name)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all services"""
        if not self._initialized:
            self.initialize()
        return self._services.copy()
    
    def get_all_repositories(self) -> Dict[str, Any]:
        """Get all repositories"""
        if not self._initialized:
            self.initialize()
        return self._repositories.copy()


# Global container instance
_container = None


def get_container(db: SQLAlchemy = None) -> DependencyContainer:
    """Get dependency container instance (Singleton pattern)"""
    global _container
    if _container is None and db is not None:
        _container = DependencyContainer(db)
        _container.initialize()
    return _container


def set_container(container: DependencyContainer):
    """Set dependency container instance (for testing)"""
    global _container
    _container = container 