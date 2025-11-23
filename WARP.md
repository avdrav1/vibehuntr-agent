# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Core workflows & commands

### One-command local app startup (recommended)

```bash
# From repo root
cp .env.example .env  # if not present yet; then edit with keys
./start_app.sh        # starts FastAPI backend + React frontend
```

Stop/restart helpers (from root):

```bash
./stop_app.sh
./restart_app.sh
```

### Manual local app startup

Backend (FastAPI, uvicorn):

```bash
# From repo root
uv run uvicorn backend.app.main:app --reload --port 8000
# or from backend/
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

Frontend (React + Vite):

```bash
cd frontend
npm install        # first time
npm run dev        # http://localhost:5173
```

### Python dependencies & tooling (uv-based)

Project uses **uv** for all Python dependency management.

```bash
# Install / sync all deps from root
make install        # preferred
# or
uv sync

# Install dev deps (tests etc.)
uv sync --dev

# Run project entrypoint scripts
uv run <module_or_script>
```

### Backend tests (FastAPI + ADK)

From repo root:

```bash
# All backend tests
uv run pytest backend/tests/

# Specific backend test file
uv run pytest backend/tests/test_session_manager.py

# With coverage
uv run pytest backend/tests/ --cov=backend/app --cov-report=html
```

Global test target (unit + integration across app):

```bash
make test          # uv sync --dev, then pytest tests/unit and tests/integration
```

### Frontend tests (React + Vitest)

From `frontend/`:

```bash
npm run test            # run all tests (Vitest)
npm run test:watch      # watch mode
# Single test file
npm run test -- src/components/Message.test.tsx
```

> Note: `frontend/README.md` documents `npm run test:coverage` and `npm run type-check`, but only `test` and `test:watch` are defined in `package.json`. Prefer `npm run test`/`test:watch` unless you add the extra scripts.

### Linting & type checking (Python)

```bash
# Full lint suite (codespell, ruff, mypy), using optional "lint" extras
make lint
# Equivalent expanded form
uv sync --dev --extra lint
uv run codespell
uv run ruff check . --diff
uv run ruff format . --check --diff
uv run mypy .
```

### Frontend linting

From `frontend/`:

```bash
npm run lint
```

### Data ingestion pipeline (Vertex AI Search / RAG)

From repo root, after setting `PROJECT_ID` and provisioning dev infra:

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
make setup-dev-env      # Terraform dev infra, including datastore
make data-ingestion     # submits Vertex AI Pipelines data ingestion job
```

Details and troubleshooting: `data_ingestion/README.md`.

### CLI & agent tooling

The ADK-based event planning system exposes both CLI and conversational interfaces.

Common entrypoints (from repo root):

```bash
# Conversational AI interface (Gemini, requires GOOGLE_API_KEY or ADC)
export GOOGLE_API_KEY="your-key"  # or use ADC
uv run python app/event_planning/chat_interface.py

# Interactive menu (no auth required) for local data-model exploration
uv run python cli/interactive_menu.py

# Command-line event planner (script entrypoint from pyproject)
uv run event-planner --help
```

See `app/event_planning/README.md` and `cli/README.md` for rich examples (users, groups, events, feedback, searching, scheduling).

### Load testing (Locust)

`tests/load_test/` contains a Locust scenario for backend load/regression testing.

High-level flow:

```bash
# 1) Deploy backend remotely (dev project)
gcloud config set project <your-dev-project-id>
make deploy

# 2) In a separate shell, create an isolated env for Locust
python3 -m venv .locust_env && source .locust_env/bin/activate
pip install locust==2.31.1

# 3) Run headless load test
export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
locust -f tests/load_test/load_test.py \
  --headless -t 30s -u 5 -r 2 \
  --csv=tests/load_test/.results/results \
  --html=tests/load_test/.results/report.html
```

Details: `tests/load_test/README.md`.

### Deployment / production

The production story is standardized around GCP: **FastAPI on Cloud Run**, **React on Cloud Storage**, **secrets in Secret Manager**, and monitoring via **Cloud Logging/Trace/BigQuery**.

Quick path:

```bash
export GCP_PROJECT_ID="your-project-id"

# First-time: create secrets and bind IAM (see QUICK_DEPLOY.md / PRODUCTION_DEPLOYMENT.md)
# Then from repo root:
chmod +x scripts/deploy-production.sh
./scripts/deploy-production.sh
```

For manual/cloud-build-style flows, or custom domains, see:

- `QUICK_DEPLOY.md` – 5-minute scripted deploy
- `PRODUCTION_DEPLOYMENT.md` – deep-dive deploy guide (Cloud Run, Cloud Storage, CORS, SSL, CI/CD)
- `PRODUCTION_READINESS.md` – current readiness status and known minor issues

## High-level architecture & mental model

### Big picture

This repo implements an **event-planning agent system** built on **Google ADK**, exposed through:

- A **React + Vite SPA** (frontend/) for chat UX
- A **FastAPI backend** (backend/) providing REST + **Server-Sent Events (SSE)** APIs
- A **core ADK agent + domain model** in `app/` (event_planning, tools, repositories, business rules)
- Supporting subsystems for **RAG / Vertex AI Search ingestion** (`data_ingestion/`), **deployment/infra** (`deployment/`, `scripts/`), **CLI/TUI** (`cli/`), and **tests**.

Conceptually:

- **Frontend** manages UI state (messages, streaming flags, session switching) and talks only to the FastAPI backend.
- **Backend** translates HTTP/SSE into ADK agent calls and manages sessions and context.
- **ADK agent layer** (`app/`) owns event-planning logic, tooling integration, persistence, and domain invariants.

### React + FastAPI migration intent

The `.kiro/specs/react-migration/*` docs describe the design, requirements, and completed tasks for moving from Streamlit to the current architecture:

- **Design (`design.md`)**: diagrams and code snippets show the intended layering:
  - React SPA (`frontend/src/components`, `frontend/src/hooks/useChat.ts`, `frontend/src/services/api.ts`) drives the UI and SSE client.
  - FastAPI backend (`backend/app/api/chat.py`, `backend/app/api/sessions.py`) exposes chat and session endpoints, delegating to services.
  - `backend/app/services/session_manager.py` tracks per-session message history; `agent_service.py` wraps ADK agent invocation and streaming.
  - The existing ADK agent (in `app/event_planning/*`) is reused as an internal dependency.
- **Requirements (`requirements.md`)**: codifies behavior the system must preserve (no duplicate messages, proper streaming semantics, session management, CORS for dev vs prod, backward compatibility with existing agent tools).
- **Tasks (`tasks.md`)**: documents that the migration work (backend app, frontend app, tests, docs, Streamlit archival) is completed; treat these as the source of truth for what the system *should* already do.

When editing or extending the app, keep the separation in that spec intact:

- UI concerns stay in React; avoid “smart” logic in backend endpoints that belongs in the agent/domain.
- Backend APIs stay thin: validation, session wiring, and delegation to `AgentService`/ADK.
- ADK agent stays responsible for event-planning decisions and tool orchestration.

### Backend architecture (FastAPI layer)

Key directories (non-exhaustive, only the important layers):

- `backend/app/main.py`
  - Assembles the FastAPI app, wires routers, CORS middleware, and config.
- `backend/app/api/`
  - `chat.py` – `POST /api/chat` (non-streaming), `GET /api/chat/stream` (SSE). These:
    - Persist messages to the session manager (role + content + timestamp).
    - Invoke `AgentService` to get full responses or streamed tokens.
    - Emit SSE events of shape `{type: "token"|"done"|"error", ...}` for the frontend to consume.
  - `sessions.py` – `POST /api/sessions`, `GET /api/sessions/{id}/messages`, `DELETE /api/sessions/{id}` for chat history lifecycle.
- `backend/app/services/`
  - `session_manager.py` – in-memory session storage; provides `create_session`, `add_message`, `get_messages`, `clear_session` and is the backend’s only knowledge of “conversation history”.
  - `agent_service.py` – bridges FastAPI and ADK:
    - Loads the event-planning agent via `app.event_planning.agent_loader`.
    - Provides async methods to invoke the agent once or stream tokens by delegating to `invoke_agent_streaming` in the ADK layer.
- `backend/app/models/schemas.py`
  - Pydantic models for HTTP payloads (`Message`, `ChatRequest`, `ChatResponse`, `SessionResponse`, etc.). Ensure these stay in sync with frontend TypeScript types.
- `backend/app/core/config.py`
  - Central configuration via `pydantic-settings`.
  - Encapsulates env-driven behavior (CORS origins, environment, host/port, API keys). The `Backend Configuration` README in this directory is the reference for new env vars and behavior.

Important backend behavior hooks:

- **CORS behavior and environments**:
  - `ENVIRONMENT=development` → allows localhost ports commonly used for frontends.
  - `ENVIRONMENT=production` → requires explicit `CORS_ORIGINS` env var to list allowed origins.
- **Secrets and API keys** are read from env / Secret Manager in production (`GOOGLE_API_KEY`, `GOOGLE_PLACES_API_KEY`, etc.), but their wiring lives in config + deployment scripts, not in controllers.

### Frontend architecture (React + Vite)

Only the main structure that matters for future edits:

- `frontend/src/components/`
  - `Chat.tsx` – top-level chat container composing header, messages, and input, wired to `useChat`.
  - `Header.tsx` – branding + “new conversation” / clear actions.
  - `MessageList.tsx`, `Message.tsx` – render history; must avoid duplicates and handle streaming message updates.
  - `ChatInput.tsx` – input control; disabled while streaming.
  - `Welcome.tsx`, `ErrorMessage.tsx` – empty-state and error UX.
- `frontend/src/hooks/useChat.ts`
  - Single source of truth for chat state: `messages`, `sessionId`, `isStreaming`.
  - Encapsulates:
    - Initial session creation (`POST /api/sessions`).
    - Non-streaming calls (if used) and **SSE streaming** of `/api/chat/stream`.
    - Logic for appending tokens to the latest assistant message and marking stream completion.
- `frontend/src/services/api.ts`
  - Typed HTTP client wrapping the backend API surface; use it from hooks/components instead of sprinkling `fetch` calls.
- `frontend/src/types/index.ts`
  - Shared types matching backend models; keep these aligned when changing API surfaces.
- `frontend/vitest.config.ts` + `frontend/src/test/`
  - Vitest + Testing Library setup; tests assert things like “no duplicate messages”, “streaming updates existing message”, and correct UX behaviors.

For new frontend work, respect the above layering: add new endpoints to `services/api.ts`, expose them through hooks, and keep components presentational where possible.

### ADK agent and event-planning domain (`app/`)

The core event-planning logic is not in `backend/` but in `app/`, largely shared between CLI, conversational interface, and web backend:

- `app/agent.py` and `app/agent_engine_app.py` – entrypoints for the ADK-based agent and Agent Engine deployment.
- `app/event_planning/`
  - `models/` – strongly-typed domain models (users, groups, events, feedback, preferences, availability, venues, suggestions, etc.).
  - `services/` – business logic (planning, scoring, conflict detection, schedule search, consensus computation, etc.).
  - `repositories/` – data layer, defaulting to JSON file storage under `data/`, but abstracted via repository interfaces.
  - AI-oriented docs (e.g., `CONVERSATIONAL_AI.md`, `QUICK_REFERENCE.md`, `TROUBLESHOOTING.md`) describe how the agent is expected to behave and common tool-usage paths.
- CLI integration (`cli/`):
  - `event_planner` console script (from `pyproject.toml`) exposes all domain operations programmatically.
  - `interactive_menu.py` is a richer TUI wrapper for manual workflows.

When modifying domain behavior or adding new capabilities, do it in `event_planning/services` and `event_planning/models`, then:

- Expose the new capability as an ADK tool if needed.
- Optionally surface it through CLI (`cli/`) and/or the web chat by adjusting prompts and the agent harness.

### RAG / data ingestion subsystem

The **RAG pipeline** (`data_ingestion/`) is intentionally decoupled from the online serving path:

- `data_ingestion/data_ingestion_pipeline/*` contains Vertex AI Pipelines components.
- `data_ingestion/pyproject.toml` defines a separate package with its own dependencies (`google-cloud-aiplatform`, `kfp`, etc.).
- `data_ingestion/README.md` describes how `make setup-dev-env` provisions infra and `make data-ingestion` submits the pipeline.

If you change schema or storage conventions for documents, update both the ingestion pipeline and any retriever configuration referenced from the ADK agent.

### Deployment & environments

Deployment is GCP-centric and already wired:

- **Dev environment**:
  - Terraform configs in `deployment/terraform/dev` (invoked via `make setup-dev-env`).
  - Intended for validating infra + pipeline + Cloud Run deployment before production.
- **Production environment**:
  - `PRODUCTION_DEPLOYMENT.md` and `QUICK_DEPLOY.md` are the canonical references.
  - Secrets via Secret Manager (`GEMINI_API_KEY`, `GOOGLE_PLACES_API_KEY`), bound to Cloud Run service accounts.
  - Frontend hosted on a `gs://$GCP_PROJECT_ID-vibehuntr-frontend` bucket with website configuration and caching headers.
  - `PRODUCTION_READINESS.md` documents current test counts and known minor issues (notably timing-sensitive frontend tests).

When adding new environment variables or services, update:

- Backend config (`backend/app/core/config.py` and its README).
- Any relevant deployment docs and scripts.
- If it impacts RAG or external services, the ingestion and infra docs.

## Notes for future Warp agents

- Prefer using existing **Makefile targets** and **uv** scripts instead of hand-rolling commands; they capture required flags and environments.
- When changing API contracts between backend and frontend, update:
  - Pydantic models in `backend/app/models/schemas.py`.
  - TypeScript interfaces in `frontend/src/types/index.ts`.
  - Any affected tests in both `backend/tests/` and `frontend/src/test/`.
- For substantial architecture changes, skim `.kiro/specs/react-migration/*.md` and the root `README.md` first; they capture the intended end state of the system and the design constraints that motivated this architecture.