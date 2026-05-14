# AGENT.md — AI Coding Guide for NaijaReview Intelligence

> **Single source of truth for every AI agent working on this codebase.**
> Read this entire file before touching any code. Update the Knowledge Base
> section when you discover something future agents should know.

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| Project | NaijaReview Intelligence |
| Purpose | Review generation (Task A) + recommendation (Task B) with optional Nigerian cultural mode |
| Competition | DSN x BCT LLM Agent Challenge 3.0 |
| Team | Panthers — Testimony, Aaliyah, Shiloh |
| Language | Python 3.12 |
| Package manager | Poetry (`pyproject.toml`) + `requirements.txt` for Docker/CI |
| LLM provider | Google Gemini (`gemini-2.5-pro` generation, `gemini-2.0-flash` utility) |
| Framework | LangGraph + LangChain + FastAPI |

**Key design principle:** The system is a general review/recommendation engine by default.
Nigerian cultural context (`naija_vibe_mode=True`) is opt-in — it should never be
assumed or hardcoded outside of mode-gated branches.

---

## 2. Repository Map

```
naijareview/
├── config.py                   ← all env vars (Pydantic Settings singleton)
├── schemas/
│   ├── auth.py                 ← UserAccount, UserRegistration, UserLogin,
│   │                              TokenPayload, TokenResponse, UserSession
│   ├── user.py                 ← Review, UserHistory, Fingerprint, RegionProfile
│   ├── item.py                 ← Item, RankedItem, Candidate, Recommendation
│   ├── output.py               ← ReviewOutput, RecommendationOutput
│   ├── persona.py              ← ColdStartPersona, NigerianPersona
│   └── vibe.py                 ← VibeScore, AbegBreakdown
├── utils/
│   └── security.py             ← hash_password(), verify_password()  [IMPLEMENTED]
├── tools/
│   ├── memory.py               ← load_user_history, save_review
│   ├── fingerprint.py          ← build_behavioural_fingerprint
│   ├── region.py               ← detect_nigerian_region
│   ├── retrieval.py            ← retrieve_similar_items, retrieve_candidates_hybrid
│   ├── persona.py              ← fetch_few_shot_examples, cold_start_interview
│   ├── vibe.py                 ← run_naija_vibe_check, score_abeg_batch
│   ├── reasoning.py            ← analyse_item_for_user, rerank_candidates
│   ├── diversity.py            ← diversity_check
│   └── taxonomy.py             ← apply_nigerian_taxonomy
├── skills/
│   ├── fingerprinting.py       ← FingerprintBuilder
│   ├── region_inference.py     ← RegionInferenceEngine
│   ├── vibe_checking.py        ← NaijaVibeChecker
│   ├── persona_authoring.py    ← PersonaAuthor
│   ├── context_assembly.py     ← ContextWindowAssembler
│   ├── memory_bootstrap.py     ← ColdStartBootstrapper
│   └── [missing]               ← RegenerationStrategist  ← NOT YET CREATED
├── agents/
│   ├── task_a.py               ← TaskAState + build_task_a_graph()  [STATE DONE]
│   ├── task_b.py               ← TaskBState + build_task_b_graph()  [STATE DONE]
│   └── nodes/
│       ├── shared.py
│       ├── task_a_nodes.py     ← ALL NODES EMPTY — implementation priority
│       └── task_b_nodes.py     ← ALL NODES EMPTY
├── llm/
│   ├── router.py               ← LLMRouter (Gemini)  [IMPLEMENTED]
│   ├── clients.py              ← stub
│   └── prompts/                ← 8 Jinja templates  [ALL IMPLEMENTED]
│       ├── task_a_generate.jinja
│       ├── task_a_vibe_rewrite.jinja
│       ├── task_b_rerank.jinja
│       ├── task_b_explain.jinja
│       ├── vibe_scorer.jinja
│       ├── cold_start_turn_1.jinja
│       ├── cold_start_turn_2.jinja
│       └── cold_start_turn_3.jinja
├── memory/
│   ├── episodic.py             ← EpisodicMemory (ChromaDB)  [STUB]
│   ├── semantic.py             ← FingerprintCache (Redis/dict)  [STUB]
│   ├── working.py              ← ContextWindowBuilder  [STUB]
│   └── item_index.py           ← FAISS wrapper  [STUB]
├── nigerian_lang/
│   ├── phrase_library.py       ← PhraseLibrary  [STUB]
│   ├── pidgin_mapper.py        ← PidginMapper  [STUB]
│   ├── region_signals.py       ← RegionSignals  [STUB]
│   ├── code_switching.py       ← CodeSwitcher  [STUB]
│   └── taxonomy.py             ← Taxonomy loader  [STUB]
├── api/
│   ├── main.py                 ← FastAPI app factory  [IMPLEMENTED]
│   ├── middleware.py           ← logging, request IDs  [STUB]
│   └── routes/
│       ├── health.py           ← /healthz
│       ├── task_a.py           ← POST /task-a/generate  [STUB — needs graph call]
│       ├── task_b.py           ← POST /task-b/recommend  [STUB — needs graph call]
│       └── admin.py            ← /admin/* endpoints  [STUB]
└── eval/
    ├── harness.py              ← EvalHarness  [STUB]
    ├── ablations.py            ← variant runner  [STUB]
    ├── user_study.py           ← paired output collector  [STUB]
    └── metrics/
        ├── rouge.py, bertscore.py, ndcg.py, hit_at_k.py, abeg.py  [ALL STUBS]

data/
├── taxonomy.yaml               ← Yelp→Nigerian category map  [INITIAL MAPPING]
└── phrase_library/             ← Nigerian phrases by region×sentiment  [EMPTY]

docs/
└── NTERNAL_ARCHITECTURE.md    ← full engineering spec (read this too)
```

---

## 3. Implementation Status

| Component | Owner | Status | Next action |
|-----------|-------|--------|-------------|
| `config.py` | All | ✅ Done | — |
| `utils/security.py` | Testimony | ✅ Done | — |
| `llm/router.py` (Gemini) | All | ✅ Done | — |
| All Jinja prompt templates (8) | All | ✅ Done | — |
| All schemas (auth, user, item, vibe, output, persona) | All | ✅ Done | — |
| `RegenerationStrategist` skill | Testimony | ✅ Done | — |
| `FingerprintBuilder` skill | Testimony | 🟡 Stub | Implement §5 Skill 1 |
| `RegionInferenceEngine` skill | Testimony | 🟡 Stub | Implement §5 Skill 2 |
| `NaijaVibeChecker` skill | Testimony | 🟡 Stub | Implement §5 Skill 3 |
| `PersonaAuthor` skill | Testimony | 🟡 Stub | Implement §5 Skill 4 |
| `ContextWindowAssembler` skill | Testimony | 🟡 Stub | Implement §5 Skill 5 |
| All tools (16) | Testimony | 🟡 Stubs | Implement §4 specs |
| Task A nodes (13) | Testimony | ⚪ Empty | Implement §6.3 |
| `build_task_a_graph()` | Testimony | ⚪ Empty | Wire §6.2 diagram |
| Task B nodes (16) | Aaliyah | ⚪ Empty | Implement §7 |
| `build_task_b_graph()` | Aaliyah | ⚪ Empty | Wire §7.2 diagram |
| `ColdStartBootstrapper` skill | Aaliyah | 🟡 Stub | Implement §5 Skill 6 |
| Memory layer (episodic, semantic, item index) | Aaliyah | 🟡 Stubs | Implement §10 |
| FastAPI routes (task_a, task_b, admin) | Aaliyah | 🟡 Stubs | Wire graph calls |
| Auth routes + JWT middleware | Testimony/Aaliyah | ✅ Done | — |
| Phrase library data | Shiloh | ⚪ Empty | Populate `data/phrase_library/` |
| Nigerian lang module | Shiloh | 🟡 Stubs | Implement |
| Eval harness + metrics | Aaliyah | 🟡 Stubs | Implement §12 |
| Frontend React UI | Testimony | ⚪ Not started | — |
| Synthetic corpus pipeline | Shiloh + Testimony | ⚪ Not started | — |

Legend: ⚪ Not started | 🟡 Stub/WIP | ✅ Implemented | 🔒 Tested

---

## 4. Data Flow

### Task A — Review Generation

```
POST /task-a/generate
  {user_id, item, naija_vibe_mode}
         │
         ▼
  [FastAPI] validate → build TaskAState → invoke graph
         │
         ▼
  load_history ──► build_fingerprint ──► detect_region ──► analyse_item
         │
         ▼
  apply_taxonomy ──► fetch_few_shots ──► author_persona ──► assemble_prompt
         │
         ▼
  generate_draft (Gemini 2.5 Pro)
         │
         ▼
  vibe_check (Gemini 2.0 Flash — always runs, passive or active)
         │
         ▼
  ┌──────────────────────────────────────────┐
  │  naija_vibe_mode=False → finalise        │
  │  naija_vibe_mode=True AND abeg≥0.70 → finalise │
  │  naija_vibe_mode=True AND abeg<0.70      │
  │  AND retry_count<2 → plan_regeneration ──┘
  │                        └──► back to author_persona
  └──────────────────────────────────────────┘
         │
         ▼
  finalise_output → ReviewOutput JSON
```

### Task B — Recommendation

```
POST /task-b/recommend
  {user_id|null, context_query, conversation_history, naija_vibe_mode}
         │
         ▼
  check_user_history
         │
    ┌────┴────────────────┐
    │ cold_start=True     │ cold_start=False
    ▼                     ▼
  cold_start_turn       load_history
  (3-turn loop,         build_fingerprint
   stateless — one      detect_region
   graph run per turn)       │
    │                        │
    └─────────┬──────────────┘
              ▼
  retrieve_candidates_hybrid (BM25 0.4 + semantic 0.6)
              │
  rerank (Gemini 2.5 Pro — chain-of-thought)
              │
  diversity_check (swap if score < 0.6)
              │
  apply_taxonomy_batch
              │
  generate_explanations (Gemini 2.5 Pro, tone = naija_vibe_mode)
              │
  compute_confidence
              │
    ┌─────────┴──────────┐
    │ conf≥0.75          │ conf<0.75 AND follow_up_turn<1
    ▼                    ▼
  finalise           gen_clarifying_question → return to caller
```

### Auth Flow

```
POST /auth/register
  {email, display_name, password}
         │
         ▼
  hash_password(password) → UserAccount(hashed_password=...)
  store in user registry
         │
         ▼
  issue JWT → TokenResponse

POST /auth/login
  {email, password}
         │
         ▼
  load UserAccount → verify_password(input, hashed_password)
  issue JWT → TokenResponse

Protected routes (task-a, task-b):
  Authorization: Bearer <token>
         │
         ▼
  JWT middleware → extract user_id → inject into request
```

---

## 5. Key Schemas (Quick Reference)

### VibeScore — critical field rename
`nigerian_authenticity` was renamed → **`cultural_authenticity`** to support non-Nigerian mode.
Any reference to the old name in a stub must be updated.

```python
class VibeScore(BaseModel):
    cultural_authenticity: float   # was: nigerian_authenticity
    cultural_accuracy: float
    persona_consistency: float
    abeg_score: float              # 0.4×auth + 0.35×acc + 0.25×persona
    breakdown: dict[str, str]
    scored_in_mode: Literal["passive", "active"]
```

### UserAccount — password storage rule
```python
class UserAccount(BaseModel):
    user_id: str
    email: str
    display_name: str
    hashed_password: str           # ALWAYS use hash_password() — never store plaintext
    auth_provider: Literal["local", "google", "github"]
    cultural_mode: Literal["general", "naija"]
    ...
```

### Fingerprint — 7 dimensions
```python
class Fingerprint(BaseModel):
    generosity_score: float        # mean(user_stars - platform_avg) normalised
    verbosity_score: float         # quantile rank of mean word count
    verbosity_word_range: tuple[int, int]   # (20th, 80th percentile)
    emotional_intensity: float
    emotional_style: Literal["calm","balanced","passionate","dramatic"]
    topic_focus: list[str]         # top-3 noun phrases, freq > 30%
    consistency_score: float       # Pearson(VADER sentiment, stars) → [0,1]
    recency_weight: float          # exponential decay coefficient
    naija_slang_index: float       # fraction of tokens matching phrase library
    confidence_intervals: dict[str, tuple[float, float]]
    computed_at: datetime
    review_count_at_computation: int
```

---

## 6. LLM Router

```python
from naijareview.llm.router import LLMRouter

router = LLMRouter()

# Generation tier — Gemini 2.5 Pro
# Use for: review drafts, reranking, explanations
text = router.call_with_retry("generation", prompt, max_tokens=800)

# Utility tier — Gemini 2.0 Flash
# Use for: item analysis, vibe scoring, cold-start parsing, clarifying questions
text = router.call_with_retry("utility", prompt, max_tokens=400)
```

**Env vars required:** `GEMINI_API_KEY`, `GEMINI_GENERATION_MODEL`, `GEMINI_UTILITY_MODEL`
**Errors caught:** `ResourceExhausted` (rate limit → exponential backoff), `GoogleAPIError` (retry once)

---

## 7. Security Utilities

```python
from naijareview.utils.security import hash_password, verify_password

# Registration path
hashed = hash_password(raw_password)          # bcrypt, store this
account = UserAccount(..., hashed_password=hashed)

# Login path
ok = verify_password(raw_password, account.hashed_password)
```

JWT signing/verification: use `python-jose` with `settings.jwt_secret_key`
and `settings.jwt_algorithm` ("HS256"). Token expiry: `settings.jwt_expire_minutes`.

---

## 8. Coding Conventions

### State immutability (non-negotiable)
```python
# ✅ Correct
def my_node(state: TaskAState) -> TaskAState:
    return {**state, "my_field": result}

# ❌ Wrong
def my_node(state: TaskAState) -> TaskAState:
    state["my_field"] = result
    return state
```

### Trace — every node must append
```python
state["trace"].append({
    "node": "node_name",
    "started_at": ts,
    "duration_ms": elapsed,
    "status": "ok",   # or "error" or "fallback"
    "summary": "brief description",
})
```

### Error handling — degrade gracefully, never crash
```python
try:
    result = risky_operation()
except SpecificError:
    result = safe_fallback_value
    state = {**state, "errors": state.get("errors", []) + ["risky_operation: reason"]}
```

### Mode-gating — always check before applying Nigerian context
```python
mode = "active" if state.get("naija_vibe_mode", False) else "passive"
intensity = "amplified" if (state.get("naija_vibe_mode") and state.get("retry_count", 0) > 0) else "natural"
```

### Imports
```python
from naijareview.config import settings          # singleton
from naijareview.schemas import Fingerprint, Item, VibeScore   # always from package root
from naijareview.llm.router import LLMRouter
from naijareview.utils.security import hash_password, verify_password
```

### Type annotations
Every function needs full type hints. `from __future__ import annotations` at top of every module.

---

## 9. Key Formulas & Thresholds

| Concept | Value |
|---------|-------|
| Abeg Score | `0.4 × cultural_authenticity + 0.35 × cultural_accuracy + 0.25 × persona_consistency` |
| Vibe regen threshold | `abeg_score < 0.70` — only in active mode |
| Max vibe retries | 2 |
| Task B confidence threshold | 0.75 — below triggers clarifying question |
| Min diversity score | 0.6 |
| Sufficient history | ≥ 3 reviews |
| Hybrid retrieval weights | BM25: 0.4 · Semantic: 0.6 |
| Task A confidence | `0.4 × history_sufficiency + 0.3 × persona_consistency + 0.2 × (1 − retry_penalty) + 0.1 × region_confidence` |
| Task B confidence | `0.35 × history_factor + 0.35 × alignment_factor + 0.15 × diversity + 0.15 × query_specificity` |
| JWT expiry | `settings.jwt_expire_minutes` (default 1440 = 24h) |

---

## 10. Commands Cheat Sheet

```bash
# Install base deps only (fast, no ML)
poetry install --without ml,eval

# Install everything
poetry install --with ml,eval

# Install via requirements.txt (Docker / CI)
pip install -r requirements.txt

# API server
poetry run uvicorn naijareview.api.main:app --reload --port 8000

# Tests
poetry run pytest tests/unit/ -v                          # fast, no services
poetry run pytest tests/integration/ -v -m integration    # needs ChromaDB + Redis

# Lint + format + type check
poetry run ruff check . && poetry run ruff format . && poetry run mypy naijareview/

# Docker full stack (API + ChromaDB + Redis)
docker compose up

# Docker with eval harness
docker compose --profile eval up

# Generate JWT secret
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 11. Component Ownership

| Component | Owner |
|-----------|-------|
| Tools (16), skills (Fingerprint/Region/Vibe/Persona/Context/Regen) | Testimony |
| Agent A graph + nodes | Testimony |
| Frontend React UI | Testimony |
| Auth routes + JWT middleware | Testimony (or Aaliyah) |
| Agent B graph + nodes | Aaliyah |
| ColdStartBootstrapper skill | Aaliyah |
| Memory layer (ChromaDB, FAISS, Redis cache) | Aaliyah |
| FastAPI routes + Docker | Aaliyah |
| Eval harness + metrics | Aaliyah |
| Phrase library data, Pidgin mapper, region signals | Shiloh |
| Taxonomy YAML | Shiloh |
| Synthetic corpus pipeline | Shiloh + Testimony |
| Dataset curation + EDA | Shiloh |
| Solution paper | Shiloh |

---

## 12. Rules for AI Agents

1. **Read `docs/NTERNAL_ARCHITECTURE.md` before implementing.** It is the engineering spec. Deviations require a code comment explaining why.

2. **Do NOT modify schemas without team discussion.** They are contracts — downstream code breaks silently.

3. **Do NOT add dependencies without updating both `pyproject.toml` AND `requirements.txt`.**

4. **Do NOT hardcode API keys, model names, or thresholds.** All come from `naijareview/config.py` → `.env`.

5. **Do NOT store plaintext passwords.** Always pass through `hash_password()` before creating `UserAccount`.

6. **Do NOT remove or weaken type annotations.** Codebase is strictly typed.

7. **Respect mode gating.** Nigerian context (Pidgin, region markers, taxonomy) only applies when `naija_vibe_mode=True`. The base system must work without it.

8. **VibeScore field is `cultural_authenticity`**, not `nigerian_authenticity`. Any stub referencing the old name must be updated.

9. **Test every implemented component.** Unit test → `tests/unit/`. Integration test → `tests/integration/`.

10. **Update this AGENT.md Knowledge Base** when you discover something non-obvious.

---

## 13. Open Design Decisions

1. **ChromaDB layout** — one collection per user vs single collection partitioned by `user_id`. Aaliyah decides after perf testing.
2. **Auth storage** — `UserAccount` registry needs a backing store. Simple JSON file for hackathon, SQLite/Postgres for production. Not yet decided.
3. **Synthetic corpus size** — 500–1000 reviews, depending on Gemini rate limits. Shiloh + Testimony coordinate.
4. **Trace in prod** — currently included in response; consider `?trace=true` opt-in for public demo.
5. **Cross-domain retrieval** — how aggressively to mix Amazon ↔ Yelp candidates. Aaliyah decides.
6. **Frontend state** — `useState` vs Zustand for cold-start conversation state. Aaliyah decides.
7. **OAuth** — `auth_provider` field supports google/github but OAuth flow not yet designed.

---

## 14. Knowledge Base

> Add discoveries here so future agents don't rediscover them.
> Format: `[DATE] [AGENT] — Discovery`

### Discoveries

- **[2026-05-13] [Antigravity/Claude Opus 4]** — Initial scaffold created. All packages have `__init__.py` files. LLM Router was originally Anthropic. All other modules are stubs with TODO markers.

- **[2026-05-13] [Antigravity/Claude Opus 4]** — Poetry creates `venv/` (not `.venv/`). Both gitignored. Full resolution with LangChain+spaCy+sentence-transformers is extremely slow (10+ min) — use `--without ml,eval` when not needed.

- **[2026-05-13] [Antigravity/Claude Opus 4]** — `config.py` singleton fails at import if required env vars are missing. For testing: mock settings or set a dummy env var.

- **[2026-05-14] [Claude Sonnet 4.6]** — **LLM provider switched from Anthropic to Gemini.** `llm/router.py` now uses `google-generativeai`. Env var changed from `ANTHROPIC_API_KEY` to `GEMINI_API_KEY`. Model vars: `GEMINI_GENERATION_MODEL` (default `gemini-2.5-pro`) and `GEMINI_UTILITY_MODEL` (default `gemini-2.0-flash`). Errors caught: `google.api_core.exceptions.ResourceExhausted` (rate limit) and `GoogleAPIError` (general). Update all mock/test patches accordingly.

- **[2026-05-14] [Claude Sonnet 4.6]** — **`VibeScore.nigerian_authenticity` renamed to `cultural_authenticity`** to support non-Nigerian mode. Update any stub or test that references the old field name.

- **[2026-05-14] [Claude Sonnet 4.6]** — **DB layer added** (`naijareview/db/`). SQLModel + SQLite (dev) / Postgres (prod). Two tables: `users` and `sessions`. Enum-like fields (`auth_provider`, `cultural_mode`) are plain `str` columns — Pydantic `Literal` types validate at API boundary, no SQLEnum migration pain. Switch DB by changing `DATABASE_URL` env var. `create_db_and_tables()` called on startup in `main.py`.

- **[2026-05-14] [Claude Sonnet 4.6]** — **Auth routes fully implemented** at `api/routes/auth.py`: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`. JWT signed with `python-jose`. Sessions tracked in `sessions` table with `revoked` flag for logout/revocation. `get_current_user` FastAPI dependency available for protecting any route — import from `naijareview.api.routes.auth`.

- **[2026-05-14] [Claude Sonnet 4.6]** — **`RegenerationStrategist` skill implemented** at `naijareview/skills/regeneration.py`. Takes `VibeScore + current_few_shots + RegionProfile` → returns `RegenerationPlan(target_dimension, prompt_addition, swap_few_shots, bump_intensity)`. Three private planners: `_plan_authenticity` (swap few-shots + bump intensity), `_plan_accuracy` (region-correct guidance), `_plan_persona_consistency` (tighten style/verbosity constraints). Import: `from naijareview.skills import RegenerationStrategist, RegenerationPlan`.

- **[2026-05-14] [Claude Sonnet 4.6]** — **Auth system added.** `schemas/auth.py` defines `UserAccount` (with `hashed_password`), `UserRegistration`, `UserLogin`, `TokenPayload`, `TokenResponse`, `UserSession`. `utils/security.py` provides `hash_password()` and `verify_password()` via `passlib[bcrypt]`. JWT via `python-jose[cryptography]`. Auth routes not yet created — need `api/routes/auth.py`.

- **[2026-05-14] [Claude Sonnet 4.6]** — **All 8 Jinja prompt templates improved and made mode-aware.** Key changes: (1) system prompt adapts to `naija_vibe_mode` — general English by default, Nigerian register when mode is on; (2) `vibe_scorer.jinja` outputs `cultural_authenticity` not `nigerian_authenticity`; (3) cold-start prompts no longer assume Nigerian context by default; (4) all templates now enforce `Return ONLY valid JSON` — no markdown, strict format. When implementing prompt rendering, pass `naija_vibe_mode` as a template variable.

- **[2026-05-14] [Claude Sonnet 4.6]** — **`requirements.txt` added** alongside `pyproject.toml`. Keep both in sync when adding dependencies. Poetry groups map to: base → always required; ml group → `--with ml`; eval group → `--with eval`; dev group → `--with dev` (or local only).

### Patterns

- **State immutability**: `{**state, "field": value}` — never mutate in-place.
- **Error taxonomy**: `UserNotFoundError`, `InsufficientHistoryError`, `LLMRateLimitError`, `LLMAPIError`, `RetrievalEmptyError`, `VibeScorerError` — see §14.3 of architecture doc.
- **Fallback principle**: Failed component → lower confidence, not crashed request.
- **Mode gate pattern**: `if state.get("naija_vibe_mode", False):` — always default to False.
- **Password rule**: `UserAccount.hashed_password = hash_password(raw)` — raw never persisted.

### Known Issues

- All tool implementations (16 tools in `naijareview/tools/`) are still stubs — highest priority work.
- Task A and Task B graph nodes are empty — implement after tools and skills.
- `UserAccount` registry now backed by SQLite via SQLModel (see `naijareview/db/`).
  Switch `DATABASE_URL` in `.env` to `postgres://...` for production.

---

*Last updated: 2026-05-14 by Claude Sonnet 4.6*
