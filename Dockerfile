# ──────────────────────────────────────────────
# NaijaReview Intelligence — API Container
# ──────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

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
COPY data/ data/

EXPOSE 9000

CMD ["uvicorn", "naijareview.api.main:app", "--host", "0.0.0.0", "--port", "9000"]
