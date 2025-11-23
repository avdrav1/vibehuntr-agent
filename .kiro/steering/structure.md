# Project Structure

## Root Layout

```
vibehuntr-agent/
├── app/                      # Core application code
├── data_ingestion/           # Data pipeline (separate uv project)
├── deployment/               # Infrastructure as Code
├── notebooks/                # Jupyter notebooks for prototyping
├── tests/                    # Test suites
├── .cloudbuild/              # CI/CD pipeline configs
├── .kiro/                    # Kiro AI assistant configuration
├── Makefile                  # Build automation
├── pyproject.toml            # Python project config
└── uv.lock                   # Dependency lock file
```

## Application Structure (`app/`)

```
app/
├── __init__.py
├── agent.py                  # Main agent definition (root_agent)
├── agent_engine_app.py       # Production wrapper for Agent Engine
├── retrievers.py             # RAG retrieval logic
├── templates.py              # Document formatting templates
├── app_utils/                # Shared utilities
│   ├── deploy.py             # Deployment helpers
│   ├── gcs.py                # GCS operations
│   ├── tracing.py            # OpenTelemetry setup
│   └── typing.py             # Type definitions (e.g., Feedback)
└── event_planning/           # Domain-specific feature
    ├── models/               # Data models (Event, User, Group, Feedback)
    ├── repositories/         # Data access layer (empty, ready for implementation)
    └── services/             # Business logic layer (empty, ready for implementation)
```

## Data Ingestion (`data_ingestion/`)

Separate Python project with its own `pyproject.toml` and `uv.lock`.

```
data_ingestion/
├── data_ingestion_pipeline/
│   ├── components/           # Pipeline components
│   │   ├── ingest_data.py    # Data loading
│   │   └── process_data.py   # Chunking & embedding
│   ├── pipeline.py           # Pipeline definition
│   └── submit_pipeline.py    # Pipeline submission script
├── pyproject.toml
└── uv.lock
```

## Deployment (`deployment/`)

```
deployment/
├── terraform/
│   ├── *.tf                  # Root Terraform configs
│   ├── vars/env.tfvars       # Environment variables
│   └── dev/                  # Dev environment configs
│       ├── *.tf
│       └── vars/env.tfvars
└── README.md
```

## Testing (`tests/`)

```
tests/
├── conftest.py               # Pytest configuration & fixtures
├── unit/                     # Unit tests
├── integration/              # Integration tests
│   └── *.evalset.json        # Evaluation datasets for `adk eval`
├── property/                 # Property-based tests (hypothesis)
└── load_test/                # Load testing scripts
    ├── load_test.py
    └── .results/             # Test results output
```

## Key Conventions

### Agent Definition Pattern
- Each agent app lives in its own directory (e.g., `app/`)
- Must have `__init__.py` and `agent.py`
- `agent.py` exports `root_agent` (Agent or App instance)
- Use `app = App(root_agent=...)` wrapper for production features

### Tool Definition Pattern
- Tools are Python functions with clear docstrings
- Docstrings become tool descriptions for the LLM
- Type hints are required for all parameters
- Tools can be in separate modules (e.g., `tools.py`)

### Model Organization
- Domain models use dataclasses with validation methods
- Include `to_dict()`, `from_dict()`, `to_json()`, `from_json()` methods
- Use Enums for status/type fields
- Validate in `validate()` method, not `__post_init__`

### Configuration Files
- `.env` files for secrets and environment-specific config
- `pyproject.toml` for Python dependencies and tool settings
- `deployment_metadata.json` for deployment tracking
- Terraform `.tfvars` files for infrastructure variables

### Import Conventions
- Use absolute imports from package root: `from app.agent import root_agent`
- Keep `__init__.py` files minimal
- Group imports: stdlib, third-party, local

### Testing Patterns
- Mock external services in `conftest.py`
- Integration tests use `InMemorySessionService`
- Property tests in separate `tests/property/` directory
- Evaluation datasets as `.evalset.json` files

### Observability
- All production code uses OpenTelemetry tracing
- Structured logging via Google Cloud Logging
- Feedback logged as structured JSON to BigQuery
- Use `app_utils/tracing.py` for trace setup
