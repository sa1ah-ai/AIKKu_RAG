# AIKKu RAG - Clean Architecture Implementation

## 🚀 Overview

AIKKu RAG is a Retrieval-Augmented Generation (RAG) chatbot system built with Flask and modern AI models. The project is organized using Clean Architecture principles to ensure maintainability, scalability, and testability.

---

## 🏗️ Architecture

The project follows Clean Architecture (Hexagonal Architecture), separating concerns into four main layers:

- **Presentation Layer** (`presentation/`): Handles HTTP requests, user interface, and external communication.
- **Application Layer** (`application/`): Orchestrates business operations and implements use cases.
- **Domain Layer** (`domain/`): Contains core business logic, entities, and repository interfaces.
- **Infrastructure Layer** (`infrastructure/`): Implements data persistence, AI models, and external services.

---

## 📁 Project Structure

```
AKKu_RAG/
├── app.py                      # Main application entrypoint
├── config.py                   # Centralized configuration
├── requirements.txt            # Python dependencies
├── test_architecture.py        # Architecture tests and demo
├── README.md                   # Project documentation
│
├── ai/                         # AI utilities and legacy code
│   ├── rag_server.py
│   ├── requirements.txt
│   ├── AIKKU_RAG_Demo.ipynb
│   ├── chunks/
│   ├── data/
│   ├── embeddings/
│   └── utils/
│       ├── chunking.py
│       ├── embedding.py
│       ├── generation.py
│       └── retrieval.py
│
├── application/                # Application layer
│   ├── container.py
│   └── services.py
│
├── domain/                     # Domain layer
│   ├── entities.py
│   ├── repositories.py
│   └── services.py
│
├── infrastructure/             # Infrastructure layer
│   ├── ai/
│   │   └── factories.py
│   └── database/
│       └── repositories.py
│
├── presentation/               # Presentation layer
│   └── controllers.py
│
├── database/                   # Database models (legacy)
│   └── db_model.py
│
├── templates/                  # HTML templates
│   ├── 404.html
│   ├── 500.html
│   ├── about.html
│   ├── admin_dashboard.html
│   ├── chat.html
│   ├── forgot_password.html
│   ├── home.html
│   ├── login.html
│   ├── profile.html
│   ├── reset_password.html
│   └── signup.html
│
├── static/                     # Static files (CSS)
│   ├── admin.css
│   ├── auth.css
│   ├── chat.css
│   ├── profile.css
│   └── style.css
│
├── profile_pics/               # User profile pictures
│   ├── AIKKu_Logo.png
│   ├── profile_1_20250804_223331.jpg
│
└── training_data/              # Training data files
```

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- CUDA-compatible GPU (for AI models)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AKKu_RAG
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r ai/requirements.txt
   ```

3. **Set up environment variables**
   ```powershell
   $env:DATABASE_URL="postgresql://username:password@localhost:5432/akku_db"
   $env:SECRET_KEY="your-secret-key"
   $env:FLASK_DEBUG="true"
   ```

4. **Initialize the database**
   ```python
   from database.db_model import db
   from app import create_app

   app = create_app()
   with app.app_context():
       db.create_all()
   ```

---

## 🚀 Running the Application

- **Development Mode**
  ```bash
  python app.py
  ```

- **Testing the Architecture**
  ```bash
  python test_architecture.py
  ```

---

## 🎯 Features

- User registration, authentication, and profile management
- Real-time chat with AI (RAG system)
- Chat session management (history, renaming, deletion)
- Admin dashboard: student management, training data upload, analytics
- Support for multiple AI models and retrieval strategies
- Arabic and English language support

---

## 🧩 Design Patterns Used

- **Repository Pattern**: Abstracts data access logic from business logic
- **Factory Pattern**: Centralizes AI model creation
- **Singleton Pattern**: Ensures single instances of expensive resources (models, config)
- **Dependency Injection**: Provides loose coupling and testability
- **Strategy Pattern**: Allows different AI models and retrieval strategies

---

## 🔧 Configuration

Centralized in `config.py`. Set environment variables for database and secret keys as shown above.

---

## 🧪 Testing

- Run all tests:
  ```bash
  python test_architecture.py
  ```
- Coverage includes:
  - Domain entities and business logic
  - Application services
  - Repository implementations
  - Controller functionality
  - RAG system integration

---

## 📚 API Endpoints

- **Authentication**
  - `POST /login` - User login
  - `GET /logout` - User logout
  - `POST /forgot_password` - Password reset request
- **Chat**
  - `POST /get` - Send chat message
  - `GET /api/chat_sessions` - Get user's chat sessions
  - `POST /api/new_chat_session` - Create new chat session
  - `PATCH /api/chat_sessions/<id>` - Rename chat session
  - `DELETE /api/chat_sessions/<id>` - Delete chat session
  - `GET /api/chat_messages/<id>` - Get chat messages
- **User Management**
  - `GET /profile` - Get user profile
  - `POST /profile` - Update user profile
- **Admin**
  - `GET /admin` - Admin dashboard
  - `POST /admin` - Upload training files
  - `POST /admin/edit_student/<id>` - Edit student
  - `POST /admin/delete_student/<id>` - Delete student

---

## 🤝 Contributing

- Follow Clean Architecture principles
- Write unit tests for new features
- Use dependency injection
- Document public interfaces
- Follow PEP 8 style guidelines

---

## 🚀 Deployment

**Docker (Recommended):**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

**Environment Variables:**
```powershell
$env:DATABASE_URL="postgresql://..."
$env:SECRET_KEY="your-secret-key"
$env:FLASK_DEBUG="false"
```

---

**AIKKu RAG** - Built for the future with Clean Architecture! 🚀
