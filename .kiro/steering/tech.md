# Technology Stack

## Core Framework

- **Google ADK (Agent Development Kit)**: Primary framework for building and orchestrating AI agents
- **Python**: 3.10-3.12 (3.13 not supported)
- **Package Manager**: `uv` (required for all dependency management)

## AI/ML Stack

- **LLM**: Gemini 2.5 Flash (default), Gemini 2.0 Flash
- **Embeddings**: text-embedding-005 via Vertex AI
- **Retrieval**: Vertex AI Search, Vertex AI Rank for re-ranking
- **LangChain**: Integration with Google Vertex AI components

## Infrastructure & Deployment

- **Cloud Platform**: Google Cloud Platform (GCP)
- **Deployment Targets**: Vertex AI Agent Engine, Cloud Run, GKE
- **IaC**: Terraform for infrastructure provisioning
- **CI/CD**: Google Cloud Build, GitHub Actions support
- **Storage**: Google Cloud Storage (GCS) for artifacts

## Observability

- **Tracing**: OpenTelemetry with Google Cloud Trace
- **Logging**: Google Cloud Logging
- **Analytics**: BigQuery for long-term event storage
- **Monitoring**: Looker Studio dashboards

## Development Tools

- **Testing**: pytest, pytest-asyncio, hypothesis (property-based testing)
- **Linting**: ruff (formatting + linting), mypy (type checking), codespell
- **Local Dev**: Streamlit via `adk web` playground
- **Notebooks**: Jupyter for prototyping and evaluation

## Common Commands

### Setup & Installation
```bash
make install              # Install dependencies with uv
make setup-dev-env        # Provision GCP resources with Terraform
```

### Development
```bash
make playground           # Launch Streamlit UI (port 8501, auto-reload)
make test                 # Run unit and integration tests
make lint                 # Run all code quality checks
```

### Deployment
```bash
make deploy               # Deploy agent to Agent Engine
make data-ingestion       # Run data ingestion pipeline
make register-gemini-enterprise  # Register to Gemini Enterprise
```

### Testing & Quality
```bash
uv run pytest tests/unit              # Unit tests only
uv run pytest tests/integration       # Integration tests only
uv run pytest tests/property          # Property-based tests
uv run ruff check . --diff            # Check linting
uv run ruff format . --check --diff   # Check formatting
uv run mypy .                         # Type checking
```

## Key Dependencies

- `google-adk>=1.15.0,<2.0.0`
- `langchain~=0.3.24` and related packages
- `google-cloud-aiplatform[evaluation,agent-engines]>=1.118.0`
- `opentelemetry-exporter-gcp-trace>=1.9.0`

## Configuration

- **Environment Variables**: Use `.env` files in agent directories
- **Project Config**: `pyproject.toml` for Python dependencies and tool settings
- **Build Automation**: `Makefile` for common workflows
