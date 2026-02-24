# Cozy Triage

Cozy Triage is an AI-powered graph-based task management system designed to bring peace of mind to overwhelming personal to-do lists. It uses a "brain dump" approach where users simply type out everything on their mind, and underlying AI models parse, categorize, and deduplicate these items into structured tasks, projects, and areas.

## Architecture & Technology Stack

- **Backend (API Layer)**: Django (Python). Handles authentication, session management, and orchestrates the AI pipeline.
- **Frontend (UI Layer)**: Next.js (React) with Tailwind CSS. Provides a premium, cozy, and interactive interface decoupled from the Django backend.
- **Database**: Memgraph Cloud (Graph + Vector Database). Acts as a single store for the user/task/project graph and vector embeddings (Atomic GraphRAG pattern).
- **Core AI**:
  - Anthropic Claude: Parsing brain dumps, GTD classification, and next-action suggestions.
  - Voyage AI (`voyage-3`): Generating 1024-dimensional vector embeddings for tasks to support similarity search and deduplication.

## Request Flow: Triage Pipeline

1. **Inbox**: User submits a chaotic "brain dump" text from the Next.js frontend.
2. **Parsing**: Django sends the text to Claude to parse out candidate tasks.
3. **GraphRAGContext**: Voyage AI generates embeddings. Memgraph is queried for duplicates and related context (projects/areas).
4. **Finalization**: Claude uses the retrieved context to refine the suggestions. 
5. **Review**: Suggestions are returned to the Next.js frontend where the user reviews, accepts, edits, or rejects them.
6. **Apply**: Accepted suggestions are committed to Memgraph as explicitly mapped nodes (`Task`, `Project`, `Area`) owned securely by the user.

## Running the Application Locally

The application uses a decoupled architecture. Both servers must be running for the full experience.

### 1. Start the Django Backend (Port 8000)

```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

The backend requires a configured `.env` file containing:
- `MEMGRAPH_URI`, `MEMGRAPH_USERNAME`, `MEMGRAPH_PASSWORD`
- `ANTHROPIC_API_KEY`
- `VOYAGE_API_KEY`

### 2. Start the Next.js Frontend (Port 3000)

```bash
cd frontend
npm install
npm run dev -- -p 3000
```

### Usage
- Log in or create an account via the Django backend at `http://localhost:8000/login/`.
- Navigate to the Next.js frontend at `http://localhost:3000/` to submit a brain dump and review your tasks.

## Documentation

Comprehensive project documentation, including data models, security practices, and UI philosophies, can be found in the `/implementation` directory.
