# Agentic Multimodal Document Assistant

An intelligent research assistant powered by agentic multimodal Retrieval-Augmented Generation (RAG) that helps you analyze documents, extract insights, and interact with your documents through natural language queries.

## Features

- **Document Upload & Processing**: Upload your documents with intelligent chunking and indexing
- **Multimodal RAG**: Advanced retrieval system supporting text and images from documents
- **Interactive Chat**: Natural language conversation with your research papers
- **Session Management**: Organize your research sessions and documents
- **Web Search Integration**: Supplement document knowledge with real-time web search
- **Smart Citations**: Automatic citation tracking and reference generation
- **Resizable UI**: Customizable layout with draggable panels
- **Authentication**: Secure JWT-based authentication with refresh token rotation

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database**: MongoDB
- **Vector Store**: ChromaDB
- **LLM**: OpenAI GPT-4.1-mini
- **Embeddings**: OpenAI text-embedding-3-small
- **Orchestration**: LangGraph for agentic workflows
- **Document Processing**: Unstructured.io
- **Authentication**: JWT with bcrypt password hashing

### Frontend
- **Framework**: React 19 with TypeScript
- **State Management**: Redux Toolkit
- **UI Library**: Material-UI (MUI)
- **Styling**: Tailwind CSS
- **Routing**: React Router v7
- **Data Fetching**: TanStack React Query (React Query)
- **HTTP Client**: Axios
- **Forms**: React Hook Form
- **Notifications**: React Toastify

## Key Libraries

### Backend Dependencies
- `fastapi` - Modern web framework
- `langchain` & `langchain-openai` - LLM framework
- `langgraph` - Agent orchestration
- `chromadb` - Vector database
- `pymongo` - MongoDB driver
- `python-jose` - JWT handling
- `bcrypt` - Password hashing
- `unstructured` - Document parsing
- `pydantic` - Data validation
- `uvicorn` - ASGI server

### Frontend Dependencies
- `@reduxjs/toolkit` - State management
- `@mui/material` - UI components
- `@tanstack/react-query` - Server state management
- `react-router-dom` - Routing
- `axios` - HTTP client
- `react-hook-form` - Form handling
- `jwt-decode` - JWT token decoding
- `react-toastify` - Toast notifications

## Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB
- OpenAI API key
- Tavily API key for web search
- Unstructured API key for document processing

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in backend directory (see `.env.example`)

5. Start the backend server:
```bash
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file in frontend directory (see `.env.example`)

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Environment Variables

Create a `.env` file in both backend and frontend directories. See `.env.example` files for required variables.

### Backend Environment Variables
- MongoDB connection
- JWT secret keys
- OpenAI API credentials
- Vector store configuration
- Document processing settings
- Web search API keys

### Frontend Environment Variables
- Backend API base URL

## Development

### Backend Commands
```bash
uvicorn main:app --reload
```

### Frontend Commands
```bash
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── config/           # Application settings
│   ├── crud/             # Database operations
│   ├── db/               # Database connections
│   ├── middleware/       # Authentication middleware
│   ├── rag_system/       # RAG pipeline & agents
│   ├── router/           # API endpoints
│   ├── schemas/          # Pydantic models
│   ├── services/         # Business logic
│   ├── utils/            # Helper functions
│   ├── vectorstore/      # ChromaDB management
│   └── main.py           # FastAPI application
│
├── frontend/
│   ├── src/
│   │   ├── app/          # Redux store & routing
│   │   ├── components/   # Reusable components
│   │   ├── features/     # Feature modules
│   │   ├── hooks/        # Custom React hooks
│   │   ├── layouts/      # Layout components
│   │   ├── lib/          # Utilities & configs
│   │   └── styles/       # Global styles
│   └── package.json
│
└── README.md
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Features in Detail

### Document Management
- Upload research papers (PDF, DOCX, TXT, MD)
- Automatic document chunking and vectorization
- Document status tracking (uploading, processing, indexed, failed)
- Retry failed document processing
- View document details and metadata

### RAG Pipeline
- Agentic workflow with LangGraph
- Query analysis and routing
- Hybrid search (semantic + lexical)
- LLM-based reranking
- Multi-modal retrieval (text + images)
- Citation generation
- Quality assurance checks

### Session Management
- Create and organize research sessions
- Session-specific document collections
- Conversation history per session
- Delete sessions with cleanup

### Authentication
- JWT-based authentication
- Refresh token rotation for security
- Token revocation to prevent reuse
- Secure password hashing with bcrypt
