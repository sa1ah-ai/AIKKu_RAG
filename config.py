import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class AIConfig:
    model_id: str = "google/gemma-2-2b-it"
    embedding_model: str = "all-mpnet-base-v2"
    max_tokens: int = 256
    top_k: int = 3
    context_window: int = 0
    max_context_tokens: int = 1200


@dataclass
class AppConfig:
    secret_key: str
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    csrf_time_limit: Optional[int] = None
    debug: bool = False


@dataclass
class FileConfig:
    training_data_folder: str = "training_data"
    profile_pics_folder: str = "profile_pics"
    embeddings_folder: str = "ai/embeddings"
    allowed_extensions: set = None

    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'pdf', 'md'}


class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.database = DatabaseConfig(
            url=os.environ.get('DATABASE_URL', 'postgresql://postgres:5152@localhost:5432/akku_db'),
            echo=os.environ.get('DATABASE_ECHO', 'false').lower() == 'true'
        )
        
        self.ai = AIConfig()
        
        self.app = AppConfig(
            secret_key=os.environ.get('SECRET_KEY', 'dev'),
            debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        )
        
        self.files = FileConfig()
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern for configuration"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance


# Global configuration instance
config = Config.get_instance() 