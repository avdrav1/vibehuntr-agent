# vibehuntr-agent

AI-powered event planning agent built with Google's Agent Development Kit (ADK). Features a modern React + FastAPI architecture with real-time streaming, document retrieval, and intelligent event recommendations.

Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.20.4`

## Architecture

Vibehuntr uses a modern web architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  React Frontend (Vite + TypeScript)                    │ │
│  │  - Real-time streaming UI                              │ │
│  │  - Tailwind CSS styling                                │ │
│  │  - Server-Sent Events (SSE) client                     │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────┘
                    │ HTTP/SSE
                    │
┌───────────────────▼──────────────────────────────────────────┐
│              FastAPI Backend                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  REST API + SSE Streaming                              │ │
│  │  - Session management                                  │ │
│  │  - CORS configuration                                  │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │  Google ADK Agent    │
         │  - Gemini 2.0 Flash  │
         │  - Event planning    │
         │  - Places API        │
         │  - RAG retrieval     │
         └─────────────────────┘
```

**Key Benefits:**
- ✅ **No duplicate messages** - React's explicit state management prevents UI issues
- ✅ **Real-time streaming** - Server-Sent Events provide smooth token-by-token responses
- ✅ **Production-ready** - Standard web architecture suitable for Cloud Run + Cloud Storage deployment
- ✅ **Better UX** - Responsive UI with fine-grained control over rendering
- ✅ **Maintainable** - Clear separation between frontend, backend, and agent logic

## Project Structure

This project is organized as follows:

```
vibehuntr-agent/
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components (Chat, Message, etc.)
│   │   ├── hooks/       # Custom hooks (useChat)
│   │   ├── services/    # API client
│   │   └── types/       # TypeScript types
│   └── README.md        # Frontend setup guide
├── backend/             # FastAPI backend
│   ├── app/
│   │   ├── api/         # REST endpoints (chat, sessions)
│   │   ├── services/    # Agent service, session manager
│   │   ├── models/      # Pydantic schemas
│   │   └── main.py      # FastAPI application
│   ├── tests/           # Backend tests
│   └── README.md        # Backend setup guide
├── app/                 # Core ADK agent code
│   ├── agent.py         # Main agent logic
│   ├── event_planning/  # Event planning domain
│   │   ├── models/      # Data models (Event, User, Group)
│   │   ├── services/    # Business logic
│   │   └── repositories/# Data access layer
│   └── app_utils/       # Utilities and helpers
├── data_ingestion/      # Data pipeline for RAG
├── deployment/          # Infrastructure and deployment scripts
├── tests/               # Integration and property-based tests
├── .cloudbuild/         # CI/CD pipeline configurations
├── Makefile             # Build automation
├── GEMINI.md            # AI-assisted development guide
└── pyproject.toml       # Project dependencies and configuration
```

## Features

### React + FastAPI Application

- **Real-time Streaming**: Server-Sent Events (SSE) for token-by-token response streaming
- **Link Preview Cards**: Automatic rich preview cards for URLs with metadata, images, and favicons
- **Session Management**: Persistent conversation history across page reloads
- **Modern UI**: Vibehuntr-branded interface with Tailwind CSS and glassmorphism effects
- **Error Handling**: Graceful error recovery with user-friendly messages
- **TypeScript**: Full type safety across frontend and backend
- **Responsive Design**: Works on desktop and mobile devices
- **Production Ready**: Optimized builds for Cloud Run and Cloud Storage deployment

### Agent Capabilities

- **Event Planning**: Intelligent event recommendations based on group preferences
- **Google Places Integration**: Real venue and restaurant suggestions with interactive venue links
- **Link Preview Cards**: Automatic metadata extraction and rich preview cards for shared URLs
- **Document Retrieval**: RAG-powered answers from indexed documents
- **Conversational AI**: Natural language understanding with Gemini 2.0 Flash
- **Context Retention**: Maintains conversation context across multiple turns

## Screenshots

### React + FastAPI Interface

The modern web interface features:
- Clean, responsive chat UI with Vibehuntr branding
- Real-time streaming responses with visual indicators
- Session management with conversation history
- Error handling with user-friendly messages
- Mobile-responsive design

![Chat Interface](docs/screenshots/chat-interface.png)
*Main chat interface with streaming responses*

![Welcome Screen](docs/screenshots/welcome-screen.png)
*Welcome screen with feature overview*

![Mobile View](docs/screenshots/mobile-view.png)
*Responsive mobile interface*

> **Note:** Screenshots will be added to `docs/screenshots/` directory. To capture screenshots:
> 1. Start the application locally
> 2. Take screenshots of key features
> 3. Save to `docs/screenshots/` with descriptive names
> 4. Update image paths in this README

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **Node.js 18+**: For React frontend - [Install](https://nodejs.org/)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Terraform**: For infrastructure deployment - [Install](https://developer.hashicorp.com/terraform/downloads)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


## Quick Start

### React + FastAPI Application (Recommended)

#### Option 1: One-Command Startup (Easiest)

```bash
# 1. Configure environment
cp .env.example .env  # Edit with your Google API key

# 2. Start everything
./start_app.sh

# The script will:
# - Check prerequisites
# - Install dependencies if needed
# - Start backend and frontend
# - Open your browser automatically
```

**To stop:** `./stop_app.sh`  
**To restart:** `./restart_app.sh`

#### Option 2: Manual Startup

```bash
# 1. Install dependencies
make install
cd frontend && npm install && cd ..

# 2. Configure environment
cp .env.example .env  # Edit with your API keys

# 3. Start backend (terminal 1)
uv run uvicorn backend.app.main:app --reload --port 8000

# 4. Start frontend (terminal 2)
cd frontend && npm run dev

# 5. Open http://localhost:5173
```

**📚 Detailed Setup:** See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for complete instructions.

### Legacy Streamlit Playground (Archived)

> **⚠️ Note:** The Streamlit version has been archived and replaced by the React + FastAPI implementation. The archived version is available in `archive/streamlit/` for reference only.

For testing the ADK agent directly (not recommended):

```bash
make install && make playground
```

Opens at http://localhost:8501

**Recommended:** Use the React + FastAPI application instead for the best experience.

## Commands

### Development Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch Streamlit interface for testing agent locally and remotely |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |

### React + FastAPI Commands

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000  # Start dev server
uv run pytest tests/                               # Run backend tests

# Frontend
cd frontend
npm run dev                                        # Start dev server (port 5173)
npm run build                                      # Build for production
npm run test                                       # Run frontend tests
```

### Deployment Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make deploy`        | Deploy agent to Agent Engine |
| `make register-gemini-enterprise` | Register deployed agent to Gemini Enterprise ([docs](https://googlecloudplatform.github.io/agent-starter-pack/cli/register_gemini_enterprise.html)) |
| `make setup-dev-env` | Set up development environment resources using Terraform                         |
| `make data-ingestion`| Run data ingestion pipeline in the Dev environment                                           |

For full command options and usage, refer to the [Makefile](Makefile).


## Usage

### Development Workflow

1. **Setup Environment**
   - Follow [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for complete setup instructions
   - Configure API keys in `.env` file
   - Install dependencies for both backend and frontend

2. **Local Development**
   - Start backend: `cd backend && uv run uvicorn app.main:app --reload`
   - Start frontend: `cd frontend && npm run dev`
   - Open http://localhost:5173 to test the application

3. **Customize Agent**
   - Edit agent logic in `app/agent.py`
   - Add tools in `app/event_planning/`
   - Modify UI in `frontend/src/components/`

4. **Test**
   - Backend tests: `uv run pytest backend/tests/`
   - Frontend tests: `cd frontend && npm run test`
   - Integration tests: `uv run pytest tests/integration/`

5. **Deploy**
   - See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for deployment guide
   - Use `./scripts/deploy-production.sh` for automated deployment
   - Backend deploys to Cloud Run, frontend to Cloud Storage + CDN

### Legacy Streamlit Workflow (Archived)

> **⚠️ Note:** This workflow is archived. Use the React + FastAPI workflow above for new development.

The original template followed a "bring your own agent" approach with Streamlit:

1. **Prototype:** Build your Generative AI Agent using the intro notebooks in `notebooks/` for guidance.
2. **Integrate:** Import your agent into the app by editing `app/agent.py`.
3. **Test:** Explore your agent functionality using the Streamlit playground (archived in `archive/streamlit/`).
4. **Deploy:** Set up CI/CD pipelines. For streamlined infrastructure deployment, run `uvx agent-starter-pack setup-cicd`.
5. **Monitor:** Track performance using Cloud Logging, Tracing, and Looker Studio dashboards.

The project includes a `GEMINI.md` file that provides context for AI tools like Gemini CLI when asking questions about your template.

## Documentation

### Setup Guides

- **[Development Setup](DEVELOPMENT_SETUP.md)** - Complete guide for local development setup
- **[Backend README](backend/README.md)** - FastAPI backend setup and API documentation
- **[Frontend README](frontend/README.md)** - React frontend setup and development guide
- **[Environment Variables](ENVIRONMENT_VARIABLES.md)** - All configuration options explained

### Feature Documentation

- **[Link Preview Cards](.kiro/specs/link-preview-cards/README.md)** - Comprehensive guide to the link preview feature including configuration, troubleshooting, and API reference
- **[Venue Links Feature](frontend/VENUE_LINKS_FEATURE.md)** - Documentation for the venue links integration with Google Places
- **[Error Handling Demo](frontend/ERROR_HANDLING_DEMO.md)** - Error handling patterns and examples

### Deployment Guides

- **[Production Deployment](PRODUCTION_DEPLOYMENT.md)** - Complete production deployment guide
- **[Production Quickstart](PRODUCTION_QUICKSTART.md)** - 5-minute deployment guide
- **[Production Checklist](PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist
- **[Deployment Scripts](scripts/)** - Automated deployment and rollback scripts

### Architecture & Design

- **[React Migration Design](.kiro/specs/react-migration/design.md)** - Architecture overview and design decisions
- **[React Migration Requirements](.kiro/specs/react-migration/requirements.md)** - Feature requirements
- **[React Migration Tasks](.kiro/specs/react-migration/tasks.md)** - Implementation plan

### Testing

- **[Integration Tests Summary](INTEGRATION_TESTS_SUMMARY.md)** - Overview of integration tests
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/src/test/`
- Property-based tests: `tests/property/`

## Deployment

> **Note:** For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform, you can use the [`agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently supports GitHub with both Google Cloud Build and GitHub Actions as CI/CD runners.

### Dev Environment

You can test deployment towards a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make deploy
```


The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Production Deployment

#### ✅ Production Ready

The application is **production-ready** with comprehensive testing, monitoring, and deployment infrastructure. See [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for the full assessment.

#### Quick Deploy (5 Minutes)

```bash
# 1. Set project ID
export GCP_PROJECT_ID="your-project-id"

# 2. Authenticate
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# 3. Create secrets
echo "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo "your-places-api-key" | gcloud secrets create GOOGLE_PLACES_API_KEY --data-file=-

# 4. Deploy
./scripts/deploy-production.sh
```

See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for the complete 5-minute guide.

#### Production Documentation

- **[Quick Deploy Guide](QUICK_DEPLOY.md)** - 5-minute deployment walkthrough
- **[Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)** - Complete deployment documentation
- **[Production Readiness Assessment](PRODUCTION_READINESS.md)** - Detailed readiness report
- **Deployment Scripts**:
  - `scripts/deploy-production.sh` - Automated deployment
  - Backend: Cloud Run (auto-scaling, serverless)
  - Frontend: Cloud Storage (static hosting, CDN-ready)

#### Infrastructure (Terraform)

For advanced infrastructure setup, see [deployment/README.md](deployment/README.md) for Terraform configurations.


## Monitoring and Observability
> You can use [this Looker Studio dashboard](https://lookerstudio.google.com/reporting/46b35167-b38b-4e44-bd37-701ef4307418/page/tEnnC
) template for visualizing events being logged in BigQuery. See the "Setup Instructions" tab to getting started.

The application uses OpenTelemetry for comprehensive observability with all events being sent to Google Cloud Trace and Logging for monitoring and to BigQuery for long term storage.
