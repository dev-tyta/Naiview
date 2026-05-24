# ──────────────────────────────────────────────
# NaijaReview Intelligence — API Container
# ──────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ─── System dependencies ─────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Python dependencies ─────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Download spaCy model ────────────────────
RUN python -m spacy download en_core_web_sm

# ─── Application code ────────────────────────
COPY naijareview/ naijareview/
COPY data/phrase_library/ data/phrase_library/
COPY data/taxonomy.yaml data/taxonomy.yaml

# ─── Install package (no deps, already installed) ─
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:9000/healthz').raise_for_status()"

CMD ["uvicorn", "naijareview.api.main:app", "--host", "0.0.0.0", "--port", "9000"]
