# 🇳🇬 NaijaReview Intelligence

**Nigerian-contextualised review generation & recommendation system**

*DSN x BCT LLM Agent Challenge 3.0 — Team Panthers*

---

## What is this?

Two LangGraph state machines that generate personalised, culturally-authentic Nigerian reviews (Task A) and recommendations (Task B). The system uses behavioural fingerprinting, regional inference, and a Naija Vibe Mode that ensures outputs sound authentically Nigerian.

## Architecture at a Glance

```
Client → FastAPI → Agent A (Review) / Agent B (Recommendation)
                     ↓                    ↓
              Shared Infrastructure Layer
              ├── ChromaDB (episodic memory)
              ├── FAISS (item index)
              ├── Fingerprint Cache (Redis/memory)
              ├── Nigerian Language Module
              └── LLM Router (Sonnet 4 / Haiku)
```

## Team

| Member | Owns |
|--------|------|
| **Testimony** | Tools, Skills (Fingerprint, Region, Vibe, Persona, Context), Agent A graph, Frontend |
| **Aaliyah** | Agent B graph, Cold-start, Retrieval stack, FastAPI, Docker, Eval harness |
| **Shiloh** | Dataset curation, Phrase library, Pidgin mapper, Taxonomy, Synthetic corpus, User study, Paper |

## Quick Start

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) installed
- (Optional) Docker & Docker Compose for full stack

### Setup

```bash
# Clone the repo
git clone https://github.com/dev-tyta/Naiview.git
cd Naiview

# Install core dependencies (fast — no ML/eval deps)
poetry install --without ml,eval

# OR install everything (slow — includes spaCy, ChromaDB, FAISS, etc.)
poetry install --with ml,eval

# Copy environment template
cp .env.example .env
# Edit .env with your Anthropic API key

# Install pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest

# Start the API server (dev)
poetry run uvicorn naijareview.api.main:app --reload --port 9000
```

### Docker (full stack)

```bash
docker compose up
```

This starts the API, ChromaDB, and Redis. Access the API at `http://localhost:9000`.

### Eval harness

```bash
docker compose --profile eval up
```

## Project Structure

See [`docs/NTERNAL_ARCHITECTURE.md`](docs/NTERNAL_ARCHITECTURE.md) for the full engineering specification.

```
naijareview/              # Main Python package
├── schemas/              # Pydantic models (the type system)
├── tools/                # 16 LangChain @tool functions
├── skills/               # Higher-level cognitive capabilities
├── agents/               # LangGraph state machines (Task A, Task B)
├── llm/                  # Two-tier router + Jinja prompt templates
├── memory/               # Episodic (ChromaDB), Semantic (cache), Working
├── nigerian_lang/        # Phrase library, Pidgin mapper, region signals
├── api/                  # FastAPI app + routes
└── eval/                 # Evaluation harness + metrics
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/task-a/generate` | POST | Generate a personalised Nigerian review |
| `/task-b/recommend` | POST | Get personalised recommendations |
| `/healthz` | GET | Health check |
| `/admin/index-stats` | GET | ChromaDB + FAISS stats |

## Key Concepts

- **Behavioural Fingerprint**: 7-dimensional profile (generosity, verbosity, emotional intensity, topic focus, consistency, recency, Naija slang index)
- **Naija Vibe Mode**: Toggle that amplifies Nigerian register — regenerates up to 2× if Abeg score < 0.70
- **Abeg Score**: `0.4 × authenticity + 0.35 × cultural_accuracy + 0.25 × persona_consistency`
- **Cold-Start**: 3-turn onboarding interview for users without history

## Development

```bash
# Lint
poetry run ruff check .

# Format
poetry run ruff format .

# Type check
poetry run mypy naijareview/

# Tests (unit only, fast)
poetry run pytest tests/unit/ -v

# Tests (integration, requires services)
poetry run pytest tests/integration/ -v -m integration
```

## AI Agents

This project is designed for agentic development. See [`AGENT.md`](AGENT.md) for the AI coding guide.

---

*NaijaReview Intelligence v0.1.0 | Team Panthers | May 2026*
