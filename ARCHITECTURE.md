# AIKKu RAG - Clean Architecture Implementation

## Overview

This document outlines the architectural patterns and design patterns implemented in the AIKKu RAG project to enhance maintainability, scalability, and collaboration.

## Architectural Pattern: Clean Architecture (Hexagonal Architecture)

### Why Clean Architecture?

Clean Architecture was chosen for this project because it:

1. **Separation of Concerns**: Clearly separates business logic from infrastructure and presentation
2. **Testability**: Makes unit testing easier with dependency inversion
3. **Independence**: Business logic is independent of frameworks, databases, and external agencies
4. **Maintainability**: Changes in one layer don't affect others
5. **Scalability**: Easy to add new features without modifying existing code

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  (Controllers, Views, HTTP handling, User Interface)        │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                         │
│  (Use Cases, Application Services, Orchestration)           │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                            │
│  (Business Logic, Entities, Domain Services, Repositories)  │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                       │
│  (Database, External Services, AI Models, File System)      │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Presentation Layer (`presentation/`)
- **Purpose**: Handle HTTP requests, user interface, and external communication
- **Components**: Controllers, route handlers, view logic
- **Dependencies**: Application services only
- **Key Files**:
  - `presentation/controllers.py` - HTTP request handlers
  - `presentation/views.py` - Template rendering logic

#### 2. Application Layer (`application/`)
- **Purpose**: Orchestrate business operations, implement use cases
- **Components**: Application services, use cases, command handlers
- **Dependencies**: Domain services and repositories
- **Key Files**:
  - `application/services.py` - Service implementations
  - `application/container.py` - Dependency injection container

#### 3. Domain Layer (`domain/`)
- **Purpose**: Core business logic, entities, and business rules
- **Components**: Entities, domain services, repository interfaces
- **Dependencies**: None (pure business logic)
- **Key Files**:
  - `domain/entities.py` - Business entities and value objects
  - `domain/repositories.py` - Repository interfaces
  - `domain/services.py` - Domain service interfaces

#### 4. Infrastructure Layer (`infrastructure/`)
- **Purpose**: External concerns, data persistence, AI models
- **Components**: Database implementations, AI model factories, file system
- **Dependencies**: Domain interfaces
- **Key Files**:
  - `infrastructure/database/repositories.py` - SQLAlchemy implementations
  - `infrastructure/ai/factories.py` - AI model factories

## Design Patterns Implemented

### 1. Repository Pattern
**Purpose**: Abstract data access logic from business logic

**Implementation**:
```python
# Domain interface
class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

# Infrastructure implementation
class SQLAlchemyUserRepository(UserRepository):
    def get_by_id(self, user_id: int) -> Optional[User]:
        user_model = UserModel.query.get(user_id)
        return self._to_domain(user_model) if user_model else None
```

**Benefits**:
- Easy to switch between different data sources
- Testable with mock repositories
- Business logic doesn't depend on specific database technology

### 2. Factory Pattern
**Purpose**: Create complex objects (AI models) with consistent configuration

**Implementation**:
```python
class HuggingFaceModelFactory(AIModelFactory):
    def create_llm_model(self, model_id: str) -> AutoModelForCausalLM:
        if model_id not in self._models:
            self._models[model_id] = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.float16, device_map="auto"
            )
        return self._models[model_id]
```

**Benefits**:
- Centralized model creation logic
- Singleton pattern for expensive models
- Easy to add new model types

### 3. Singleton Pattern
**Purpose**: Ensure single instances of expensive resources (AI models, configuration)

**Implementation**:
```python
class Config:
    @classmethod
    def get_instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

# Global configuration instance
config = Config.get_instance()
```

**Benefits**:
- Prevents multiple model loading
- Consistent configuration across application
- Memory efficiency

### 4. Dependency Injection Pattern
**Purpose**: Provide dependencies to components without tight coupling

**Implementation**:
```python
class DependencyContainer:
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self._repositories = {}
        self._services = {}
    
    def initialize(self):
        self._initialize_repositories()
        self._initialize_services()
    
    def get_service(self, name: str):
        return self._services.get(name)
```

**Benefits**:
- Loose coupling between components
- Easy to test with mock dependencies
- Centralized dependency management

### 5. Strategy Pattern
**Purpose**: Allow different AI models and retrieval strategies

**Implementation**:
```python
class RAGSystem:
    def __init__(self, llm_model, tokenizer, embedding_model, config):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.retriever = None  # Set by dependency injection
    
    def process_query(self, query: RAGQuery) -> RAGResponse:
        retrieved_chunks = self.retriever.retrieve(query.query)
        prompt = self._build_prompt(query, retrieved_chunks)
        answer = self._generate_response(prompt)
        return RAGResponse(answer=answer, sources=retrieved_chunks)
```

**Benefits**:
- Easy to swap different AI models
- Configurable retrieval strategies
- Extensible for new AI capabilities

### 6. Observer Pattern (Planned)
**Purpose**: Handle chat session events and notifications

**Implementation** (Future):
```python
class ChatEventObserver(ABC):
    @abstractmethod
    def on_message_sent(self, message: ChatMessage):
        pass

class NotificationObserver(ChatEventObserver):
    def on_message_sent(self, message: ChatMessage):
        # Send notifications
        pass
```

### 7. Command Pattern (Planned)
**Purpose**: Handle complex chat operations as commands

**Implementation** (Future):
```python
class SendMessageCommand:
    def __init__(self, session_id: int, message: str, user_id: int):
        self.session_id = session_id
        self.message = message
        self.user_id = user_id
    
    def execute(self):
        # Execute the command
        pass
```

## Configuration Management

### Centralized Configuration (`config.py`)
```python
@dataclass
class AIConfig:
    model_id: str = "google/gemma-2-2b-it"
    embedding_model: str = "all-mpnet-base-v2"
    max_tokens: int = 256
    top_k: int = 3

class Config:
    def __init__(self):
        self.ai = AIConfig()
        self.database = DatabaseConfig(...)
        self.app = AppConfig(...)
```

**Benefits**:
- Environment-based configuration
- Type-safe configuration
- Centralized settings management

## File Structure

```
AIKKu_RAG/
├── config.py                 # Configuration management
├── app_new.py               # New main application (Clean Architecture)
├── app.py                   # Legacy application
├── domain/                  # Domain layer
│   ├── __init__.py
│   ├── entities.py          # Business entities
│   ├── repositories.py      # Repository interfaces
│   └── services.py          # Domain service interfaces
├── application/             # Application layer
│   ├── __init__.py
│   ├── services.py          # Service implementations
│   └── container.py         # Dependency injection container
├── infrastructure/          # Infrastructure layer
│   ├── database/
│   │   └── repositories.py  # SQLAlchemy implementations
│   └── ai/
│       └── factories.py     # AI model factories
├── presentation/            # Presentation layer
│   ├── __init__.py
│   └── controllers.py       # HTTP controllers
├── ai/                      # AI utilities (legacy)
│   ├── rag_server.py
│   └── utils/
├── database/                # Database models (legacy)
│   └── db_model.py
└── templates/               # HTML templates
```

## Migration Strategy

### Phase 1: ✅ Completed
- [x] Create domain entities and interfaces
- [x] Implement repository pattern
- [x] Create application services
- [x] Implement dependency injection
- [x] Create AI model factories
- [x] Implement controllers

### Phase 2: 🔄 In Progress
- [ ] Complete repository implementations
- [ ] Add comprehensive error handling
- [ ] Implement logging strategy
- [ ] Add unit tests

### Phase 3: 📋 Planned
- [ ] Implement Observer pattern for events
- [ ] Add Command pattern for complex operations
- [ ] Implement caching strategy
- [ ] Add monitoring and metrics
- [ ] Performance optimization

## Benefits of the New Architecture

### 1. Maintainability
- **Clear Separation**: Each layer has a single responsibility
- **Easy Debugging**: Issues can be isolated to specific layers
- **Code Organization**: Related functionality is grouped together

### 2. Scalability
- **Horizontal Scaling**: Services can be deployed independently
- **Feature Addition**: New features don't affect existing code
- **Performance**: AI models can be optimized independently

### 3. Testability
- **Unit Testing**: Each layer can be tested in isolation
- **Mock Dependencies**: Easy to mock external dependencies
- **Integration Testing**: Clear boundaries for integration tests

### 4. Collaboration
- **Team Development**: Different teams can work on different layers
- **Code Reviews**: Clear interfaces make reviews more effective
- **Documentation**: Architecture is self-documenting

## Usage Examples

### Running the New Application
```bash
# Use the new clean architecture application
python app_new.py

# Or use the legacy application
python app.py
```

### Adding a New Feature
1. **Domain Layer**: Define entities and interfaces
2. **Infrastructure Layer**: Implement repository/data access
3. **Application Layer**: Create service implementation
4. **Presentation Layer**: Add controller and routes

### Testing
```python
# Example unit test with dependency injection
def test_chat_service():
    mock_repo = MockChatSessionRepository()
    mock_rag = MockRAGService()
    service = ChatServiceImpl(mock_repo, mock_rag)
    
    result = service.send_message(1, "Hello", SenderType.STUDENT)
    assert result is not None
```

## Conclusion

The implementation of Clean Architecture with design patterns provides:

1. **Better Code Organization**: Clear separation of concerns
2. **Improved Maintainability**: Changes are localized to specific layers
3. **Enhanced Testability**: Easy to test components in isolation
4. **Scalability**: Easy to add new features and scale components
5. **Team Collaboration**: Different teams can work on different layers

This architecture serves as a solid foundation for the AIKKu RAG project's future growth and evolution. 