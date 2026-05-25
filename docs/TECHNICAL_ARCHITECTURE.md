# Naiview Intelligence — Technical Architecture Document

**DSN × BCT LLM Agent Challenge 3.0 · Team Panthers**  
**Authors:** Testimony Adekoya · Aaliyah · Shiloh  
**Version:** 1.0 · May 2026

---

## 1. System Overview

Naiview Intelligence is a two-agent LangGraph system that performs culturally-aware Nigerian user modelling. Each agent is an independent stateful graph sharing a common infrastructure layer.

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent A | LangGraph + Gemini 2.5 Pro | Review generation |
| Agent B | LangGraph + Gemini 2.5 Pro | Cross-domain recommendation |
| NLM | PhraseLibrary + PidginMapper + CodeSwitcher | Register shifting |
| Naija Vibe Checker | Composite scorer | Cultural authenticity scoring |
| Vector store | ChromaDB (Railway) | Episodic user memory |
| Item index | FAISS (IndexFlatIP, 384-dim) | Candidate retrieval |
| Embeddings | BAAI/bge-base-en-v1.5 | Semantic encoding |
| LLM utility tier | Gemini 2.0 Flash | Reranking, cold-start, rating inference |
| Fingerprint cache | In-memory / Redis | 24 h TTL per user |
| API | FastAPI + uvicorn | REST endpoints |

---

## 2. Design Principles

**1. Reasoning-first.** Both agents traverse deliberate graph steps. The LLM is called multiple times per request — never once. Conditional edges handle cold-start divergence, low confidence, and cultural regeneration.

**2. Explicit typed state.** Both agents use `TypedDict` state schemas. State is immutable across nodes — each node returns a new state dict. No global mutation.

**3. Naija Vibe Mode is opt-in.** The Vibe Checker always *scores* (passive mode) but only *regenerates* when `naija_vibe_mode=True`. Enforced at state-schema level, not as a post-hoc string replacement.

**4. Two-tier LLM.** Gemini 2.5 Pro for generation (quality ceiling). Gemini 2.0 Flash for utility calls (rerank, parse, infer). Minimises latency and cost without sacrificing output quality.

**5. Evaluation-first.** Every component is tested through the harness. Numbers are the ground truth.

---

## 3. Seven-Dimensional Behavioural Fingerprint

The fingerprint is the primary user model. It is computed from review history and cached for 24 hours.

| Dimension | Description | Computation |
|-----------|-------------|-------------|
| **Generosity** | Mean star rating vs platform average | `mean(stars) / 3.0` normalised |
| **Verbosity** | Quantile rank of word count in user history | `scipy.stats.percentileofscore` |
| **Emotional intensity** | Density of intensifier phrases | Phrase library match count / word count |
| **Topic focus** | Top-3 noun phrases across reviews | spaCy `noun_chunks`, TF-IDF ranked |
| **Consistency** | Pearson correlation of sentiment score to star rating | `scipy.stats.pearsonr` on VADER compound |
| **Recency weight** | Exponential decay coefficient for recent reviews | `λ = 0.1`, `w_i = e^{-λ·Δdays_i}` |
| **Naija Slang Index** | Fraction of review tokens matching phrase library | `len(matches) / total_tokens` |

The fingerprint drives: persona authoring, verbosity constraints in the prompt, few-shot selection, and the Vibe Checker calibration.

---

## 4. Agent A — Review Generation (12 Nodes)

### 4.1 Graph topology

```
load_history → build_fingerprint → detect_region → analyse_item
    → apply_taxonomy → fetch_few_shots → author_persona
    → assemble_prompt → generate_draft → vibe_check
    → [finalise_output | plan_regeneration → author_persona]
```

`plan_regeneration` loops back to `author_persona` up to 2 times when Abeg Score < 0.70.

### 4.2 Node specifications

| Node | Input | Output | LLM? |
|------|-------|--------|------|
| `load_history` | `user_id` | `review_history[]` | No — ChromaDB |
| `build_fingerprint` | `review_history[]` | `BehaviouralFingerprint` | No — computed |
| `detect_region` | `review_history[]` | `region, region_confidence` | No — pattern match |
| `analyse_item` | `item_id` | `ItemMetadata` | No — FAISS + metadata |
| `apply_taxonomy` | `ItemMetadata` | `nigerian_category` | No — `taxonomy.yaml` |
| `fetch_few_shots` | `fingerprint, region` | `few_shots[]` | No — ChromaDB retrieval |
| `author_persona` | `fingerprint, region, regen_hint?` | `persona_block` | **Gemini Flash** |
| `assemble_prompt` | all above | `prompt_text` | No — Jinja2 template |
| `generate_draft` | `prompt_text` | `draft_review, draft_rating` | **Gemini 2.5 Pro** |
| `vibe_check` | `draft_review` | `abeg_score, dimensions` | No — rule-based scorer |
| `plan_regeneration` | `abeg_score, dimensions` | `regen_hint` | **Gemini Flash** |
| `finalise_output` | `draft_review, draft_rating` | `review, rating, vibe_score, trace` | **Gemini Flash** (polish + rating infer) |

### 4.3 Prompt architecture

The generation prompt (`task_a_generate.jinja`) is structured in six sections:

1. **System role** — culturally-aware Nigerian reviewer (vibe ON) or standard reviewer (vibe OFF)
2. **User fingerprint** — all 7 dimensions with values
3. **Region block** — regional markers (if detected, confidence ≥ 0.6)
4. **Item block** — name, category, Nigerian taxonomy label, attributes
5. **Few-shots** — up to 3 authentic reference reviews from ChromaDB
6. **Persona instruction** — authored persona block from `author_persona` node

Constraints appended:
- Word count: `min(verbosity_word_range[0], 50)` words minimum
- Rating must reflect review sentiment — not inferred independently
- Return valid JSON only: `{"review": "...", "rating": 1.0–5.0}`

### 4.4 Naija Vibe Checker

**Abeg Score** = 0.40 × cultural_authenticity + 0.35 × cultural_accuracy + 0.25 × persona_consistency

| Dimension | What it measures |
|-----------|-----------------|
| `cultural_authenticity` | Phrase library coverage, Pidgin marker density, hedge-free intensity |
| `cultural_accuracy` | Regional marker correctness, taxonomy alignment |
| `persona_consistency` | Star rating ↔ sentiment coherence, verbosity fit |

Threshold: Abeg < 0.70 → trigger `plan_regeneration`. Maximum 2 regeneration loops. Third output accepted regardless.

### 4.5 Nigerian Language Module (NLM)

Three components operating as a post-generation register shifter:

- **PhraseLibrary** — 847-token Pidgin/Nigerian English phrase lexicon, region-tagged
- **PidginMapper** — replaces standard English constructs with Pidgin equivalents at the appropriate Slang Index density
- **CodeSwitcher** — inserts mid-sentence language switches (e.g. "e sweet die", "no cap", "abeg") calibrated to the user's Naija Slang Index

The NLM is only applied when `naija_vibe_mode=True` and Slang Index > 0.2.

---

## 5. Agent B — Recommendation (14 Nodes)

### 5.1 Graph topology — two entry paths

```
[Existing user]
load_history → build_fingerprint → detect_region
    ↘
      retrieve_candidates → rerank → apply_diversity
    ↗                           → cold_start_conversation (3-turn)
[New user]
```

Both paths merge at `retrieve_candidates`.

### 5.2 Cold-start conversation

For users with no Nigerian ChromaDB history (< 3 reviews), Agent B initiates a 3-turn structured conversation:

| Turn | Question | Parsed signal |
|------|---------|--------------|
| 1 | Food/category preferences | `food_preference` |
| 2 | Atmosphere and setting | `atmosphere_preference` |
| 3 | Budget range | `budget_range` |

The conversation output bootstraps a low-confidence fingerprint (`confidence ≤ 0.60`). The fingerprint is flagged as `cold_start=True` and excluded from the cache write-back.

### 5.3 Hybrid retrieval

`retrieve_candidates` combines:
- **BM25** (weight 0.4): lexical match over item descriptions and category tags
- **Semantic** (weight 0.6): cosine similarity via BAAI/bge-base-en-v1.5 embeddings against FAISS IndexFlatIP

Score: `hybrid = 0.4 × BM25_score + 0.6 × semantic_score`

Top-K = 20 candidates retrieved; `rerank` node reduces to 5 final recommendations.

### 5.4 Chain-of-thought reranking

The reranker prompt (Gemini Flash) instructs the model to:
1. Score each candidate against the user fingerprint (1–10)
2. Explain the match in 1 sentence
3. Flag candidates that duplicate category/region (diversity check)
4. Return ranked JSON array

The reranker operates on the full 20-candidate set and returns the top 5 with reasons.

### 5.5 Confidence model

Confidence is reported per recommendation:

```
confidence = 0.4 × (ChromaDB knowledge score)
           + 0.35 × (persona clarity score)
           + 0.25 × (region match score)
```

Cold-start sessions start at `confidence = 0.45` and increment as turns complete.

---

## 6. Infrastructure

### 6.1 ChromaDB (episodic memory)

- Hosted: Railway managed instance
- Collection: `naijareview_episodes`
- Document schema: `{user_id, review_text, item_id, category, stars, region, timestamp}`
- Dict metadata (not nested objects — ChromaDB constraint)
- Used for: few-shot retrieval (Agent A), user history lookup (Agent B)

### 6.2 FAISS item index

- Model: `BAAI/bge-base-en-v1.5` (384-dim, CPU-optimised)
- Index type: `IndexFlatIP` (exact inner product / cosine similarity)
- Size: ~52,000 items from integrated dataset
- Metadata: stored as parallel JSON (`item_display_metadata.json`)
- Rebuild script: `scripts/rebuild_bge_index.py` (~2 min on CPU)

### 6.3 LLM router

Two-tier strategy via `LLMRouter`:

| Tier | Model | Used for |
|------|-------|---------|
| Generation | `gemini-2.5-pro` | `generate_draft`, complex reasoning |
| Utility | `gemini-2.0-flash` | `author_persona`, `plan_regeneration`, `rerank`, `finalise_output` |

Router includes retry logic (`max_retries=2`, exponential backoff) and token budget enforcement (`max_tokens=8192`).

### 6.4 API

FastAPI application at `naijareview/api/main.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/task-a/generate` | POST | Full review generation pipeline |
| `/task-b/recommend` | POST | Recommendation pipeline (existing user) |
| `/task-b/cold-start` | POST | Cold-start conversation turn |
| `/healthz` | GET | Liveness check |
| `/admin/results` | GET | Latest eval results JSON |

Singletons (FAISS, ChromaDB, embedder, graphs) are loaded at startup via `warm_up()` — startup latency ~58s, subsequent requests ~2–4s.

---

## 7. Data Flow Diagram

```
User Request
    │
    ▼
FastAPI Route
    │
    ├──[Task A]──▶ LangGraph Agent A
    │                  │
    │                  ├─ ChromaDB (history + few-shots)
    │                  ├─ FAISS (item metadata)
    │                  ├─ Fingerprint Cache (Redis/memory)
    │                  ├─ Gemini 2.5 Pro (generate_draft)
    │                  ├─ Gemini Flash (author_persona, finalise)
    │                  └─ NLM (register shift)
    │
    └──[Task B]──▶ LangGraph Agent B
                       │
                       ├─ ChromaDB (history)
                       ├─ FAISS + BM25 (retrieve_candidates)
                       ├─ Gemini Flash (rerank, cold-start)
                       └─ Confidence model
    │
    ▼
JSON Response
{review_text, rating, vibe_score, fingerprint, reasoning_trace}
```

---

## 8. Repository Layout

```
naijareview/
├── agents/
│   ├── task_a.py              # Agent A graph builder
│   ├── task_b.py              # Agent B graph builder
│   ├── nodes/
│   │   ├── task_a_nodes.py    # All 12 Agent A nodes
│   │   └── task_b_nodes.py    # All 14 Agent B nodes
│   └── state/
│       ├── task_a_state.py    # TypedDict for Agent A
│       └── task_b_state.py    # TypedDict for Agent B
├── api/
│   ├── main.py                # FastAPI app + lifespan
│   ├── startup.py             # Singleton warm-up
│   ├── middleware.py          # Request ID + logging
│   └── routes/
│       ├── task_a.py          # /task-a/* routes
│       ├── task_b.py          # /task-b/* routes
│       ├── admin.py           # /admin/results
│       └── health.py          # /healthz
├── llm/
│   ├── router.py              # Two-tier LLM router
│   └── prompts/               # Jinja2 templates
├── memory/
│   ├── fingerprint.py         # Fingerprint computation
│   ├── embedding.py           # EmbeddingProvider (multi-model)
│   └── item_index.py          # FAISS wrapper
├── nlm/
│   ├── phrase_library.py      # 847-token lexicon
│   ├── pidgin_mapper.py       # Register shifter
│   └── code_switcher.py       # Code-switch injector
├── tools/
│   ├── retrieval.py           # BM25 + semantic hybrid
│   └── vibe_checker.py        # Abeg Score computation
└── config.py                  # Pydantic settings
data/
├── phrase_library/            # Pidgin phrase files by region
├── processed/
│   ├── faiss_index_bge_opt    # FAISS index (384-dim)
│   └── item_display_metadata.json
└── taxonomy.yaml              # Nigerian category taxonomy
tests/
└── eval/
    └── harness.py             # 6-variant ablation harness
```

---

*NaijaReview Intelligence v0.1.0 · DSN × BCT Hackathon 3.0 · Team Panthers*
