# ──────────────────────────────────────────────
# NaijaReview Intelligence — API Container
# ──────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# ─── Install system dependencies ─────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ─── Install Poetry ──────────────────────────
RUN pip install --no-cache-dir poetry==1.8.4

# ─── Copy dependency files first (cache layer) ─
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --with ml

# ─── Copy application code ───────────────────
COPY naijareview/ naijareview/
COPY data/phrase_library/ data/phrase_library/
COPY data/taxonomy.yaml data/taxonomy.yaml

# ─── Install package ─────────────────────────
RUN poetry install --with ml

# ─── Download spaCy model ────────────────────
RUN python -m spacy download en_core_web_sm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()"

CMD ["uvicorn", "naijareview.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
