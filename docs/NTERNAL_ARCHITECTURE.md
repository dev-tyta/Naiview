# NaijaReview Intelligence — Internal Engineering Architecture

**DSN x BCT LLM Agent Challenge 3.0 | Internal Technical Specification**
**Version 2.0 | 13 May 2026**
**Audience: Testimony, Aaliyah, Shiloh**

---

## How to read this document

This is the engineering spec we code against — not the user-facing proposal. Every tool, skill, node, edge, prompt, and schema the team builds is defined here. If something is ambiguous, this document is wrong and needs an issue raised.

The proposal sells the *what* and *why*. This document defines the *how*.

Structure:

1. System overview and design principles
2. Repository layout
3. Data layer — storage, schemas, indexes
4. Tool catalog — every LangChain tool, fully specified
5. Skill catalog — higher-level cognitive capabilities the agents possess
6. Agent A (Task A) — state schema and full LangGraph specification
7. Agent B (Task B) — state schema and full LangGraph specification
8. Naija Vibe Mode — toggle propagation, active vs passive behaviour
9. Prompt architecture — context window layouts and templates
10. Memory engineering — three-tier model, lifecycle, persistence
11. LLM orchestration — two-tier strategy
12. Evaluation harness internals
13. API contracts
14. Observability, error handling, and fallbacks
15. Open questions

---

## 1. System Overview & Design Principles

### 1.1 What we are building

Two LangGraph state machines (Agent A for review generation, Agent B for recommendation) that share an infrastructure layer (vector stores, fingerprint cache, Nigerian language module, LLM router). Each agent is a graph of typed nodes connected by conditional edges. Outputs are returned with structured confidence metadata.

### 1.2 Five non-negotiable design principles

1. **Reasoning-first, not pipeline.** Both agents traverse a graph of deliberate steps. Conditional edges handle low confidence, cold-start divergence, and regeneration. The LLM is called multiple times per request — never once.
2. **Explicit state.** Both agents use typed state schemas (`TypedDict`). State is immutable across nodes — each node returns a new state with its computed fields filled in. No global mutation.
3. **Tools have contracts.** Every tool has a declared input schema, output schema, and failure mode. Tools are LangChain `@tool` decorated functions with Pydantic-typed I/O. The agent calls tools through the graph — not inline.
4. **Naija Vibe Mode is opt-in.** The Vibe Checker module always *scores* (passive mode), but only *regenerates* when the user has activated Naija Vibe Mode in their request. This separation is enforced at the state-schema level.
5. **Eval harness is the spine.** Every component is tested through the harness from Day 1. If a change breaks the harness numbers, it doesn't ship.

### 1.3 Component map

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│                    React UI + REST clients + API tests                   │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ HTTPS / JSON
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                   │
│             FastAPI: POST /task-a/generate, POST /task-b/recommend       │
│             + /healthz, /metrics, /admin/index-stats                     │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          AGENT ORCHESTRATION                             │
│                                                                          │
│   ┌──────────────────────────┐      ┌──────────────────────────────┐   │
│   │   AGENT A (LangGraph)    │      │     AGENT B (LangGraph)      │   │
│   │   Review Generation       │      │     Recommendation            │   │
│   │   State: TaskAState       │      │     State: TaskBState         │   │
│   └────────────┬─────────────┘      └────────────┬─────────────────┘   │
│                │                                  │                      │
│                └──────────────┬───────────────────┘                      │
│                               │                                          │
│                               ▼                                          │
│             ┌─────────────────────────────────────┐                      │
│             │       SHARED TOOL REGISTRY          │                      │
│             │   (16 LangChain tools, see §4)      │                      │
│             └─────────────────────────────────────┘                      │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       SHARED INFRASTRUCTURE                              │
│                                                                          │
│   ┌─────────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │  ChromaDB   │  │   FAISS    │  │  Fingerprint │  │   LLM Router  │   │
│   │  Episodic   │  │   Item     │  │   Cache      │  │  Sonnet/Haiku │   │
│   │  Memory     │  │   Index    │  │   (Redis or  │  │   + Fallback  │   │
│   │  (per user) │  │  (global)  │  │   in-memory) │  │               │   │
│   └─────────────┘  └────────────┘  └──────────────┘  └──────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              NIGERIAN LANGUAGE MODULE                            │   │
│   │   AfriSenti phrase library | Pidgin expression mapper |          │   │
│   │   Region detector signals | Code-switching patterns |            │   │
│   │   Taxonomy overlay (Yelp → Nigerian categories)                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Request lifecycle at a glance

```
Client → POST /task-a/generate {user_id, item_metadata, naija_vibe_mode: bool}
       → FastAPI handler validates payload
       → Initialises TaskAState with inputs
       → Invokes Agent A LangGraph
       → Graph traverses nodes (each one a function: state → state)
       → Nodes call tools as needed (which hit Chroma/FAISS/LLM)
       → Conditional edges route based on score thresholds
       → Final state contains review + rating + confidence + metadata
       → Handler returns JSON response
```

---

## 2. Repository Layout

```
naijareview/
├── README.md
├── pyproject.toml                  # Poetry / hatch project config
├── docker-compose.yml              # API + ChromaDB + Redis (eval profile)
├── Dockerfile                      # API container
├── .env.example
│
├── naijareview/                    # Main Python package
│   ├── __init__.py
│   ├── config.py                   # Pydantic Settings (env vars, thresholds)
│   ├── schemas/                    # Pydantic models — the type system
│   │   ├── __init__.py
│   │   ├── user.py                 # UserHistory, Fingerprint, RegionProfile
│   │   ├── item.py                 # Item, RankedItem, Candidate
│   │   ├── output.py               # ReviewOutput, RecommendationOutput
│   │   ├── persona.py              # ColdStartPersona, NigerianPersona
│   │   └── vibe.py                 # VibeScore, AbegBreakdown
│   │
│   ├── tools/                      # LangChain tools (§4)
│   │   ├── __init__.py
│   │   ├── memory.py               # load_user_history, save_user_history
│   │   ├── fingerprint.py          # build_behavioural_fingerprint
│   │   ├── region.py               # detect_nigerian_region
│   │   ├── retrieval.py            # retrieve_similar_items, retrieve_candidates
│   │   ├── persona.py              # fetch_few_shot_examples, cold_start_interview
│   │   ├── vibe.py                 # run_naija_vibe_check, score_abeg
│   │   ├── reasoning.py            # analyse_item, rerank_candidates
│   │   ├── diversity.py            # diversity_check
│   │   └── taxonomy.py             # apply_nigerian_taxonomy
│   │
│   ├── skills/                     # Higher-level cognitive skills (§5)
│   │   ├── __init__.py
│   │   ├── fingerprinting.py       # FingerprintBuilder class
│   │   ├── region_inference.py     # RegionInferenceEngine
│   │   ├── vibe_checking.py        # NaijaVibeChecker
│   │   ├── persona_authoring.py    # PersonaAuthor
│   │   ├── context_assembly.py     # ContextWindowAssembler
│   │   └── memory_bootstrap.py     # ColdStartBootstrapper
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── task_a.py               # Agent A graph definition (§6)
│   │   ├── task_b.py               # Agent B graph definition (§7)
│   │   └── nodes/                  # Node implementations
│   │       ├── shared.py           # Nodes used by both agents
│   │       ├── task_a_nodes.py
│   │       └── task_b_nodes.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── router.py               # Two-tier router (Sonnet vs Haiku)
│   │   ├── prompts/                # Prompt templates as files (§9)
│   │   │   ├── task_a_generate.jinja
│   │   │   ├── task_a_vibe_rewrite.jinja
│   │   │   ├── task_b_rerank.jinja
│   │   │   ├── task_b_explain.jinja
│   │   │   ├── cold_start_turn_1.jinja
│   │   │   ├── cold_start_turn_2.jinja
│   │   │   ├── cold_start_turn_3.jinja
│   │   │   └── vibe_scorer.jinja
│   │   └── clients.py              # Anthropic client wrappers + retry logic
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── episodic.py             # ChromaDB wrapper for user history
│   │   ├── semantic.py             # Fingerprint cache wrapper
│   │   ├── working.py              # Context window builder
│   │   └── item_index.py           # FAISS wrapper for items
│   │
│   ├── nigerian_lang/
│   │   ├── __init__.py
│   │   ├── phrase_library.py       # AfriSenti phrase loader
│   │   ├── pidgin_mapper.py        # English → Pidgin phrase mapping
│   │   ├── region_signals.py       # Regional marker dictionaries
│   │   ├── code_switching.py       # Yoruba/Igbo/Hausa loanword injection
│   │   └── taxonomy.py             # Yelp → Nigerian category map
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── routes/
│   │   │   ├── task_a.py
│   │   │   ├── task_b.py
│   │   │   ├── admin.py
│   │   │   └── health.py
│   │   └── middleware.py           # Logging, request IDs, error handling
│   │
│   └── eval/
│       ├── __init__.py
│       ├── harness.py              # Main eval orchestrator
│       ├── metrics/
│       │   ├── rouge.py
│       │   ├── bertscore.py
│       │   ├── ndcg.py
│       │   ├── hit_at_k.py
│       │   └── abeg.py
│       ├── ablations.py            # Variant runner
│       └── user_study.py           # Paired-output collector
│
├── data/
│   ├── raw/                        # Downloaded datasets (gitignored)
│   ├── processed/                  # Cleaned, indexed (gitignored)
│   ├── phrase_library/             # Curated Nigerian phrases (versioned)
│   ├── synthetic/                  # Synthetic corpus (versioned, small)
│   └── taxonomy.yaml               # Yelp → Nigerian category map (versioned)
│
├── notebooks/
│   ├── 01_eda_yelp.ipynb
│   ├── 02_eda_amazon.ipynb
│   ├── 03_afrisenti_mining.ipynb
│   ├── 04_synthetic_generation.ipynb
│   └── 05_results_analysis.ipynb
│
├── frontend/                       # React UI
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── FingerprintRadar.tsx
│   │   │   ├── ReasoningTrace.tsx
│   │   │   ├── NaijaVibeToggle.tsx
│   │   │   ├── ColdStartChat.tsx
│   │   │   └── ConfidenceBadge.tsx
│   │   └── api/client.ts
│
├── tests/
│   ├── unit/
│   │   ├── test_fingerprint.py
│   │   ├── test_region_detection.py
│   │   ├── test_vibe_check.py
│   │   └── test_taxonomy.py
│   ├── integration/
│   │   ├── test_task_a_graph.py
│   │   ├── test_task_b_graph.py
│   │   └── test_cold_start.py
│   └── eval/
│       └── test_harness.py
│
└── docs/
    ├── INTERNAL_ARCHITECTURE.md    # This document
    ├── PROPOSAL.md                 # User-facing
    ├── TASK_SPLIT.md
    └── api_contracts.md
```

---

## 3. Data Layer

### 3.1 Storage components

| Store | Backed by | Holds | Lifecycle |
|---|---|---|---|
| Episodic Memory | ChromaDB collection per user | All past reviews, embedded + metadata | Persistent, append-only |
| Item Index | FAISS flat index + metadata sidecar | All items (Yelp + Amazon), embedded | Built once at data-prep, rebuilt on dataset refresh |
| Fingerprint Cache | Redis (prod) / Python dict (dev) | Computed `Fingerprint` per user_id | Persistent, recomputed on new review |
| Phrase Library | JSON files in repo | AfriSenti-derived Nigerian phrases by region × sentiment | Versioned in git |
| Taxonomy | YAML in repo | Yelp categories → Nigerian categories | Versioned in git |
| Synthetic Corpus | JSONL files | Generated reviews, Abeg ≥ 0.75 | Versioned in git (small files) |

### 3.2 Core Pydantic schemas

These are the contracts every tool and node operates on. Defined in `naijareview/schemas/`.

```python
# schemas/user.py

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class Review(BaseModel):
    review_id: str
    user_id: str
    item_id: str
    text: str
    stars: float = Field(ge=1.0, le=5.0)
    timestamp: datetime
    item_category: str

class UserHistory(BaseModel):
    user_id: str
    reviews: list[Review]
    review_count: int
    earliest_review: datetime | None
    latest_review: datetime | None

    @property
    def has_sufficient_history(self) -> bool:
        return self.review_count >= 3

class Fingerprint(BaseModel):
    user_id: str
    generosity_score: float = Field(ge=0.0, le=1.0)
    verbosity_score: float = Field(ge=0.0, le=1.0)
    verbosity_word_range: tuple[int, int]
    emotional_intensity: float = Field(ge=0.0, le=1.0)
    emotional_style: Literal["calm", "balanced", "passionate", "dramatic"]
    topic_focus: list[str]  # e.g. ["food", "service", "value"]
    consistency_score: float = Field(ge=0.0, le=1.0)
    recency_weight: float = Field(ge=0.0, le=1.0)
    naija_slang_index: float = Field(ge=0.0, le=1.0)
    confidence_intervals: dict[str, tuple[float, float]]
    computed_at: datetime
    review_count_at_computation: int

class RegionProfile(BaseModel):
    user_id: str
    region: Literal["Lagos", "Abuja", "Port Harcourt", "Kano", "Enugu", "Unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    signals: list[str]  # Which phrases / mentions triggered the inference

class ColdStartPersona(BaseModel):
    user_id: str  # Anonymous ID for new users
    food_preference: str | None
    value_orientation: Literal["taste_first", "value_first", "balanced"] | None
    atmosphere_preference: Literal["lively", "quiet", "either"] | None
    budget_range: Literal["low", "mid", "high"] | None
    frequency_of_dining_out: Literal["rare", "occasional", "frequent"] | None
    turns_completed: int
```

```python
# schemas/item.py

from pydantic import BaseModel

class Item(BaseModel):
    item_id: str
    name: str
    category: str
    nigerian_category: str | None  # From taxonomy overlay
    attributes: dict[str, str]
    avg_rating: float
    review_count: int
    description: str | None

class RankedItem(BaseModel):
    item: Item
    rank: int
    alignment_score: float = Field(ge=0.0, le=1.0)
    reasoning_snippet: str  # Why this item ranks here

class Recommendation(BaseModel):
    item: Item
    rank: int
    explanation: str  # Nigerian-register reasoning shown to user
    alignment_dimensions: list[str]  # Which fingerprint dims it matches
```

```python
# schemas/vibe.py

from pydantic import BaseModel, Field

class VibeScore(BaseModel):
    nigerian_authenticity: float = Field(ge=0.0, le=1.0)
    cultural_accuracy: float = Field(ge=0.0, le=1.0)
    persona_consistency: float = Field(ge=0.0, le=1.0)
    abeg_score: float = Field(ge=0.0, le=1.0)
    breakdown: dict[str, str]  # Per-dimension qualitative notes
    scored_in_mode: Literal["passive", "active"]
```

```python
# schemas/output.py

from pydantic import BaseModel

class ReviewOutput(BaseModel):
    generated_review: str
    predicted_rating: float
    confidence: float
    fingerprint_match: str  # Human-readable summary
    style_notes: str
    abeg_score: float | None  # Always populated (passive or active)
    vibe_breakdown: dict[str, float] | None
    naija_vibe_mode_active: bool
    retry_count: int

class RecommendationOutput(BaseModel):
    recommendations: list[Recommendation]
    reasoning: str
    confidence: float
    cold_start_mode: bool
    diversity_score: float
    follow_up_question: str | None
    naija_vibe_mode_active: bool
```

---

## 4. Tool Catalog

Tools are the atomic, schema-validated capabilities the agents can call. Every tool is a `@tool`-decorated function with Pydantic input and output. Sixteen total — grouped by domain.

### 4.1 Memory tools (`tools/memory.py`)

#### `load_user_history`
- **Purpose:** Retrieve all reviews for a user from ChromaDB.
- **Input:** `user_id: str`
- **Output:** `UserHistory`
- **Side effects:** None (read-only).
- **Failure modes:** `UserNotFoundError` if user_id has no records → caller routes to cold-start flow.
- **Performance budget:** < 50ms for users with ≤ 500 reviews.

#### `save_review`
- **Purpose:** Persist a new review to episodic memory after generation (optional — used in interactive demo only).
- **Input:** `review: Review`
- **Output:** `bool` (success)
- **Side effects:** Writes to ChromaDB, invalidates fingerprint cache for user.

### 4.2 Fingerprint tools (`tools/fingerprint.py`)

#### `build_behavioural_fingerprint`
- **Purpose:** Compute the 7-dimensional fingerprint from user history. Cached.
- **Input:** `user_history: UserHistory`
- **Output:** `Fingerprint`
- **Algorithm summary:**
  - **Generosity:** mean of (user_stars − platform_avg_stars_for_category), normalised to [0,1].
  - **Verbosity:** quantile rank of mean word count across all users; word range is (20th, 80th percentile of user's review lengths).
  - **Emotional intensity:** lexicon-based — count of intensifier words ("very", "absolutely", "die", "no joke") and exclamation marks per 100 tokens, normalised. Style label is derived from intensity bucket.
  - **Topic focus:** top-3 noun phrases (extracted via spaCy) appearing across user's reviews with frequency > 30%.
  - **Consistency:** Pearson correlation between (sentiment of review text via VADER + Pidgin-aware extension) and (star rating), scaled to [0,1].
  - **Recency weight:** exponential decay over review timestamps — recent reviews get up to 2× weight in fingerprint computation. Output is the effective recency-bias coefficient.
  - **Naija slang index:** fraction of tokens in user's reviews matching the Nigerian phrase library (Pidgin + loanwords).
- **Caching:** Result cached in Redis keyed by `(user_id, last_review_timestamp)`. Cache invalidated on new review.
- **Failure modes:** If history has < 3 reviews, returns fingerprint with `confidence_intervals` set to (0.0, 1.0) for all dimensions and `topic_focus = []`. Callers should check `review_count_at_computation` before relying.

### 4.3 Region & Persona tools (`tools/region.py`, `tools/persona.py`)

#### `detect_nigerian_region`
- **Purpose:** Infer the user's likely Nigerian region from review-text signals.
- **Input:** `user_history: UserHistory`
- **Output:** `RegionProfile`
- **Algorithm:**
  1. Concatenate user's last 20 reviews.
  2. Match against a regional signal dictionary:
     - **Lagos:** mentions of VI, Lekki, Ikeja, Surulere, Yaba, "traffic", "go-slow", danfo, okada
     - **Abuja:** mentions of Wuse, Maitama, Garki, "FCT"
     - **Port Harcourt:** mentions of GRA, Trans Amadi, "PH", "Garden City", bole, seafood
     - **Kano:** mentions of Sabon Gari, suya-specific terms, Hausa loanwords (`ranka dede`, `madalla`)
     - **Enugu:** mentions of Independence Layout, Ogui, Igbo loanwords (`biko`, `nna`, `igbo`-language tokens)
  3. Score each region by signal density, return top region with confidence = (top score / sum of all scores).
  4. If max confidence < 0.4, return `region="Unknown"`.

#### `fetch_few_shot_examples`
- **Purpose:** Retrieve 3 authentic Nigerian review examples matching region, sentiment, and category from the phrase library.
- **Input:** `region: str, sentiment: Literal["positive","negative","mixed"], category: str, k: int = 3`
- **Output:** `list[str]`
- **Backend:** Pre-indexed AfriSenti + NaijaSenti + synthetic corpus, partitioned by (region, sentiment, category). Falls back to (region, sentiment, *) if exact category has too few samples.

#### `cold_start_interview`
- **Purpose:** Run one turn of the cold-start onboarding conversation. Stateful via turn_history.
- **Input:** `turn_history: list[dict]` (each dict has `role`, `content`)
- **Output:** `tuple[str, ColdStartPersona | None]` — (agent's next utterance, persona if all 3 turns complete else None)
- **Behaviour:**
  - Turn 1: ask food preference → parse user response → store `food_preference`
  - Turn 2: ask value orientation → parse → store `value_orientation`
  - Turn 3: ask atmosphere + budget combined → parse → store both
  - After turn 3, set `frequency_of_dining_out = "occasional"` as default, return completed persona

### 4.4 Retrieval tools (`tools/retrieval.py`)

#### `retrieve_similar_items`
- **Purpose:** Semantic search over FAISS item index, filtered by category.
- **Input:** `query: str, category: str | None, top_k: int = 20`
- **Output:** `list[Item]`
- **Backend:** FAISS flat IP index; query embedded with `sentence-transformers/all-MiniLM-L6-v2`. Post-filter by category if provided.

#### `retrieve_candidates_hybrid`
- **Purpose:** Hybrid BM25 + semantic retrieval used for Task B candidate generation.
- **Input:** `query: str, fingerprint: Fingerprint | None, cold_start_persona: ColdStartPersona | None, top_k: int = 20`
- **Output:** `list[Item]`
- **Algorithm:**
  1. Construct BM25 query from `query` + top topic_focus words from fingerprint (if available).
  2. Construct semantic query from `query` embedded.
  3. Retrieve top-30 from each, deduplicate by `item_id`.
  4. Re-score by `0.4 × bm25_score + 0.6 × semantic_score`, return top-20.

### 4.5 Reasoning tools (`tools/reasoning.py`)

#### `analyse_item_for_user`
- **Purpose:** LLM-backed analysis of how an item maps to a user's preferences. Used in Task A before generation.
- **Input:** `item: Item, fingerprint: Fingerprint`
- **Output:** `dict` with keys: `inferred_sentiment`, `relevant_topics`, `predicted_rating_range`, `reasoning`
- **LLM tier:** Haiku (utility task).

#### `rerank_candidates`
- **Purpose:** LLM-backed chain-of-thought reranking of top-20 candidates against fingerprint.
- **Input:** `candidates: list[Item], fingerprint: Fingerprint, context_query: str`
- **Output:** `list[RankedItem]` (sorted by `alignment_score` descending)
- **LLM tier:** Sonnet 4 (quality-critical).

### 4.6 Vibe tools (`tools/vibe.py`)

#### `run_naija_vibe_check`
- **Purpose:** Score a generated review on Nigerian authenticity, cultural accuracy, persona consistency. Always runs; behaviour at threshold depends on mode.
- **Input:** `review_text: str, target_fingerprint: Fingerprint, item: Item, mode: Literal["passive","active"]`
- **Output:** `VibeScore` (includes `scored_in_mode` field)
- **Algorithm:**
  - **Nigerian authenticity:** weighted combination of (slang-token fraction matching phrase library) and (LLM-judged authenticity score from Haiku).
  - **Cultural accuracy:** LLM-judged (Haiku) — does the review reference correct regional context, food names, slang for this region/category?
  - **Persona consistency:** cosine similarity between fingerprint-derived target embedding and review embedding, mapped to [0,1].
  - **Abeg score:** `0.4 × nigerian_authenticity + 0.35 × cultural_accuracy + 0.25 × persona_consistency`.
- **Important:** The tool itself does NOT decide to retry. It returns the score. The graph's conditional edge reads `mode` and `abeg_score` and decides whether to route to regeneration.

#### `score_abeg_batch`
- **Purpose:** Run vibe check across a batch (for evaluation harness and synthetic corpus filtering).
- **Input:** `reviews: list[str], fingerprints: list[Fingerprint], items: list[Item]`
- **Output:** `list[VibeScore]`
- **Mode:** Always passive.

### 4.7 Diversity & Taxonomy tools (`tools/diversity.py`, `tools/taxonomy.py`)

#### `diversity_check`
- **Purpose:** Ensure recommended set isn't dominated by one category.
- **Input:** `ranked_items: list[RankedItem], min_diversity: float = 0.6`
- **Output:** `tuple[list[RankedItem], float]` (possibly-reordered list, diversity score)
- **Algorithm:**
  - Compute diversity = 1 − (max category count / total count).
  - If diversity < min_diversity, swap the lowest-ranked item from the dominant category with the highest-ranked item from a different category that's currently below top-5.
  - Repeat until diversity ≥ min_diversity or no swaps possible.

#### `apply_nigerian_taxonomy`
- **Purpose:** Remap an item's Yelp/Amazon category to its Nigerian equivalent.
- **Input:** `item: Item`
- **Output:** `Item` (with `nigerian_category` field filled in)
- **Backend:** YAML-loaded mapping in `data/taxonomy.yaml`. Falls back to original category if no mapping exists.

### 4.8 Tool registry summary

| Tool | LLM-backed? | Tier | Used by |
|---|---|---|---|
| `load_user_history` | No | — | A, B |
| `save_review` | No | — | A (demo only) |
| `build_behavioural_fingerprint` | No | — | A, B |
| `detect_nigerian_region` | No | — | A, B |
| `fetch_few_shot_examples` | No | — | A |
| `cold_start_interview` | Yes | Haiku | B |
| `retrieve_similar_items` | No | — | A (rare), B |
| `retrieve_candidates_hybrid` | No | — | B |
| `analyse_item_for_user` | Yes | Haiku | A |
| `rerank_candidates` | Yes | Sonnet | B |
| `run_naija_vibe_check` | Yes (partial) | Haiku | A |
| `score_abeg_batch` | Yes (partial) | Haiku | eval |
| `diversity_check` | No | — | B |
| `apply_nigerian_taxonomy` | No | — | A, B |
| `generate_review_draft` | Yes | Sonnet | A (in-node) |
| `generate_recommendation_explanations` | Yes | Sonnet | B (in-node) |

---

## 5. Skill Catalog

A **tool** is an atomic call (e.g. "retrieve top-20 items"). A **skill** is a higher-level cognitive capability that may coordinate several tools and contain business logic that doesn't belong inside any single tool. Skills are Python classes in `naijareview/skills/` — they encapsulate behaviour rather than expose tool-style APIs.

The agents call tools directly; skills are used by nodes to keep complex logic out of the graph itself.

### Skill 1: `FingerprintBuilder`

**Owns:** Computing fingerprints, managing the cache, handling cold-start vs full users.

```python
class FingerprintBuilder:
    def __init__(self, cache: FingerprintCache, episodic: EpisodicMemory):
        ...

    def get_or_build(self, user_id: str) -> Fingerprint:
        """Returns cached fingerprint if fresh, else recomputes."""

    def build_from_persona(self, persona: ColdStartPersona) -> Fingerprint:
        """Bootstraps a fingerprint from cold-start onboarding answers.
        Maps persona answers to fingerprint dimensions with low confidence
        intervals (because we have no behavioural evidence yet)."""

    def invalidate(self, user_id: str) -> None:
        """Called after new review is saved."""
```

### Skill 2: `RegionInferenceEngine`

**Owns:** Detecting region from history; also detecting from a single sentence (for cold-start where the user mentioned a place).

```python
class RegionInferenceEngine:
    def from_history(self, history: UserHistory) -> RegionProfile: ...
    def from_text(self, text: str) -> RegionProfile: ...
    def boost_with_explicit_signal(self, profile: RegionProfile, hint: str) -> RegionProfile:
        """If user typed 'I'm in Lagos' anywhere, increase confidence."""
```

### Skill 3: `NaijaVibeChecker`

**Owns:** Computing Vibe Scores, knowing about active vs passive mode, deciding regeneration eligibility.

```python
class NaijaVibeChecker:
    def __init__(self, llm_router: LLMRouter, phrase_library: PhraseLibrary):
        self.regen_threshold = 0.70  # From config
        self.max_retries = 2

    def score(self, review_text: str, fingerprint: Fingerprint,
              item: Item, mode: Literal["passive","active"]) -> VibeScore: ...

    def should_regenerate(self, score: VibeScore, retry_count: int,
                          mode: Literal["passive","active"]) -> bool:
        """Returns True only if mode == 'active' AND score < threshold
        AND retry_count < max_retries."""

    def regeneration_hint(self, score: VibeScore) -> str:
        """Returns the prompt-additive hint for the next generation attempt,
        based on which sub-score was weakest."""
```

### Skill 4: `PersonaAuthor`

**Owns:** Translating a fingerprint + region + item into a structured persona-prompt block that the generation LLM consumes.

```python
class PersonaAuthor:
    def author(self, fingerprint: Fingerprint, region: RegionProfile,
               item: Item, intensity: Literal["natural","amplified"]) -> str:
        """Returns the persona-section text for the prompt.
        intensity='amplified' is used when Naija Vibe Mode is active and we're
        retrying after a low score — it dials up the Nigerian register
        instructions and selects stronger few-shot examples."""
```

### Skill 5: `ContextWindowAssembler`

**Owns:** Building the final prompt for the LLM by assembling segments in the documented order, with token budgeting.

```python
class ContextWindowAssembler:
    def __init__(self, max_tokens: int = 1000):
        ...

    def assemble_task_a(self, fingerprint: Fingerprint, region: RegionProfile,
                        item: Item, few_shots: list[str],
                        persona_block: str, regen_hint: str | None) -> str: ...

    def assemble_task_b_rerank(self, fingerprint: Fingerprint,
                                candidates: list[Item],
                                context_query: str) -> str: ...

    def truncate_if_needed(self, segments: list[str], budget: int) -> str:
        """If over budget, drop few-shots first, then truncate fingerprint
        verbosity range to a single number, etc."""
```

### Skill 6: `ColdStartBootstrapper`

**Owns:** Running the multi-turn onboarding loop, validating user responses, building the final persona, and seeding a low-confidence fingerprint.

```python
class ColdStartBootstrapper:
    def __init__(self, llm_router: LLMRouter, fingerprint_builder: FingerprintBuilder):
        self.required_turns = 3

    def next_turn(self, conversation_history: list[dict]) -> tuple[str, ColdStartPersona | None]:
        """Returns (agent_utterance, persona_if_complete)."""

    def is_complete(self, history: list[dict]) -> bool: ...

    def finalise(self, history: list[dict]) -> tuple[ColdStartPersona, Fingerprint]:
        """Returns the persona and a bootstrapped low-confidence fingerprint."""
```

### Skill 7: `RegenerationStrategist` (used only when Naija Vibe is active)

**Owns:** Deciding *how* to regenerate when Vibe Mode is on and score is low. Different weak sub-scores need different fixes.

```python
class RegenerationStrategist:
    def plan(self, vibe_score: VibeScore, current_few_shots: list[str],
             region: RegionProfile) -> RegenerationPlan:
        """Returns a plan with:
          - which dimension to target
          - whether to swap few-shots (and to what)
          - whether to bump intensity in PersonaAuthor
          - extra prompt instructions to inject"""
```

### Why this split matters

Tools are stateless functions. Skills hold the logic that's too complex for a tool but doesn't belong in a node either (because it'd duplicate across nodes). When Aaliyah's eval harness wants to test fingerprinting alone, it imports `FingerprintBuilder` directly without spinning up the whole graph. When Shiloh's synthetic corpus pipeline wants to filter outputs by Abeg score, it imports `NaijaVibeChecker` directly.

---

## 6. Agent A — Review Generation (Task A)

### 6.1 State schema

```python
# agents/task_a.py

from typing import TypedDict, Literal, Optional
from naijareview.schemas import (
    UserHistory, Fingerprint, RegionProfile, Item, VibeScore
)

class TaskAState(TypedDict, total=False):
    # ─── Inputs (set by API handler) ───────────────────────
    user_id: str
    item: Item
    naija_vibe_mode: bool                      # Default False

    # ─── Loaded / computed in-graph ────────────────────────
    user_history: Optional[UserHistory]
    fingerprint: Optional[Fingerprint]
    region_profile: Optional[RegionProfile]
    item_analysis: Optional[dict]              # Output of analyse_item_for_user
    few_shot_examples: list[str]
    persona_block: Optional[str]
    assembled_prompt: Optional[str]

    # ─── Generation state ──────────────────────────────────
    draft_review: Optional[str]
    draft_rating: Optional[float]
    vibe_score: Optional[VibeScore]
    retry_count: int                           # Default 0
    regeneration_hint: Optional[str]           # Used to amplify next attempt

    # ─── Output ────────────────────────────────────────────
    final_review: Optional[str]
    final_rating: Optional[float]
    confidence: Optional[float]
    fingerprint_match_summary: Optional[str]
    style_notes: Optional[str]

    # ─── Error / diagnostic ────────────────────────────────
    errors: list[str]
    trace: list[dict]                          # Per-node timing + outputs
```

### 6.2 Full LangGraph specification

```
                          ┌──────────────────┐
                          │      START       │
                          └────────┬─────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: load_history             │
                  │  ─────────────────────────────  │
                  │  Tool: load_user_history        │
                  │  Sets: user_history             │
                  │  On miss: raise UserNotFoundErr │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: build_fingerprint        │
                  │  ─────────────────────────────  │
                  │  Skill: FingerprintBuilder      │
                  │  Sets: fingerprint              │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: detect_region            │
                  │  ─────────────────────────────  │
                  │  Skill: RegionInferenceEngine   │
                  │  Sets: region_profile           │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: analyse_item             │
                  │  ─────────────────────────────  │
                  │  Tool: analyse_item_for_user    │
                  │  LLM: Haiku                     │
                  │  Sets: item_analysis            │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: apply_taxonomy           │
                  │  ─────────────────────────────  │
                  │  Tool: apply_nigerian_taxonomy  │
                  │  Mutates: item.nigerian_category│
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: fetch_few_shots          │
                  │  ─────────────────────────────  │
                  │  Tool: fetch_few_shot_examples  │
                  │  Args: region, sentiment        │
                  │        (from item_analysis),    │
                  │        category                 │
                  │  Sets: few_shot_examples        │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: author_persona           │
                  │  ─────────────────────────────  │
                  │  Skill: PersonaAuthor           │
                  │  Args: intensity = "amplified"  │
                  │        if retry_count > 0 AND   │
                  │        naija_vibe_mode          │
                  │        else "natural"           │
                  │  Sets: persona_block            │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: assemble_prompt          │
                  │  ─────────────────────────────  │
                  │  Skill: ContextWindowAssembler  │
                  │  Sets: assembled_prompt         │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: generate_draft           │
                  │  ─────────────────────────────  │
                  │  LLM: Sonnet 4                  │
                  │  Sets: draft_review,            │
                  │        draft_rating             │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: vibe_check               │
                  │  ─────────────────────────────  │
                  │  Skill: NaijaVibeChecker        │
                  │  Mode: "active" if              │
                  │        naija_vibe_mode          │
                  │        else "passive"           │
                  │  Sets: vibe_score               │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ╔═══════════════════════════════╗
                  ║  CONDITIONAL EDGE              ║
                  ║  decide_after_vibe_check       ║
                  ╚═══════════════════════════════╝
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
            ▼                      ▼                      ▼
  naija_vibe_mode == False    naija_vibe_mode == True   naija_vibe_mode == True
  (always finalise)           AND abeg ≥ 0.70          AND abeg < 0.70
                              (finalise)               AND retry_count < 2
                                                       (regenerate)
            │                      │                      │
            └──────────┬───────────┘                      │
                       ▼                                  ▼
        ┌────────────────────────────┐    ┌────────────────────────────┐
        │  Node: finalise_output      │    │  Node: plan_regeneration    │
        │  ─────────────────────────  │    │  ─────────────────────────  │
        │  Computes confidence,       │    │  Skill: RegenerationStrate. │
        │  fingerprint_match summary, │    │  Sets: regeneration_hint    │
        │  style_notes                │    │  Increments retry_count     │
        └─────────────┬──────────────┘    └─────────────┬──────────────┘
                      │                                  │
                      ▼                                  │
                  ┌───────┐                              │
                  │  END  │                              │
                  └───────┘                              │
                                                         │
                                          Back to: author_persona
                                          (loop with intensity="amplified")
```

### 6.3 Node implementations (key details)

```python
# agents/nodes/task_a_nodes.py

def load_history(state: TaskAState) -> TaskAState:
    try:
        history = load_user_history.invoke({"user_id": state["user_id"]})
        return {**state, "user_history": history, "trace": [...]}
    except UserNotFoundError:
        # Task A assumes user exists. If not, this is a misuse — Task B
        # handles cold-start, not Task A. Return error and END.
        return {**state, "errors": ["user_not_found"], "final_review": None}

def vibe_check(state: TaskAState) -> TaskAState:
    mode = "active" if state.get("naija_vibe_mode", False) else "passive"
    score = checker.score(
        review_text=state["draft_review"],
        fingerprint=state["fingerprint"],
        item=state["item"],
        mode=mode,
    )
    return {**state, "vibe_score": score}

def decide_after_vibe_check(state: TaskAState) -> Literal["finalise_output", "plan_regeneration"]:
    if not state.get("naija_vibe_mode", False):
        return "finalise_output"
    if state["vibe_score"].abeg_score >= 0.70:
        return "finalise_output"
    if state.get("retry_count", 0) >= 2:
        return "finalise_output"  # Out of retries; ship what we have
    return "plan_regeneration"

def plan_regeneration(state: TaskAState) -> TaskAState:
    strategist = RegenerationStrategist()
    plan = strategist.plan(
        vibe_score=state["vibe_score"],
        current_few_shots=state["few_shot_examples"],
        region=state["region_profile"],
    )
    return {
        **state,
        "regeneration_hint": plan.prompt_addition,
        "few_shot_examples": plan.new_few_shots or state["few_shot_examples"],
        "retry_count": state.get("retry_count", 0) + 1,
    }

def finalise_output(state: TaskAState) -> TaskAState:
    fingerprint = state["fingerprint"]
    vibe = state["vibe_score"]

    # Confidence is a composite signal
    confidence = (
        0.4 * min(1.0, fingerprint.review_count_at_computation / 20.0)  # History sufficiency
        + 0.3 * vibe.persona_consistency
        + 0.2 * (1.0 - state.get("retry_count", 0) * 0.2)                # Fewer retries = higher conf
        + 0.1 * state["region_profile"].confidence
    )

    return {
        **state,
        "final_review": state["draft_review"],
        "final_rating": state["draft_rating"],
        "confidence": round(confidence, 2),
        "fingerprint_match_summary": _summarise_match(fingerprint, state["item"]),
        "style_notes": _summarise_style(fingerprint),
    }
```

### 6.4 Failure & fallback paths

| Failure | Detection | Recovery |
|---|---|---|
| `user_not_found` in `load_history` | `UserNotFoundError` caught | Set error, return empty output, log to trace |
| Fingerprint cache miss | Caught in `FingerprintBuilder.get_or_build` | Recompute synchronously; populate cache |
| `analyse_item_for_user` LLM error | Anthropic API exception | Retry once with Haiku; if still fails, use default `item_analysis = {sentiment: "neutral"}` |
| `generate_draft` LLM error | Anthropic API exception | Retry once; if still fails, set `errors`, return empty output |
| Vibe Check LLM portion fails | Exception in `run_naija_vibe_check` | Compute lexical components only, mark `cultural_accuracy` as 0.5 (unknown), include warning in trace |
| Max retries exhausted (Vibe Mode active, score still low) | `retry_count >= 2` in conditional | Finalise anyway with the best draft so far; flag in `style_notes` |

---

## 7. Agent B — Recommendation (Task B)

### 7.1 State schema

```python
class TaskBState(TypedDict, total=False):
    # ─── Inputs ────────────────────────────────────────────
    user_id: Optional[str]                     # None for cold-start
    context_query: str                          # What they want now
    conversation_history: list[dict]            # For multi-turn
    naija_vibe_mode: bool                       # Affects explanation tone

    # ─── Loaded / computed in-graph ────────────────────────
    user_history: Optional[UserHistory]
    fingerprint: Optional[Fingerprint]
    region_profile: Optional[RegionProfile]
    is_cold_start: bool
    cold_start_persona: Optional[ColdStartPersona]
    cold_start_turn_count: int                  # Default 0

    # ─── Retrieval & ranking state ─────────────────────────
    candidate_pool: list[Item]                  # Top-20 raw
    reranked_candidates: list[RankedItem]
    diversity_score: Optional[float]

    # ─── Output ────────────────────────────────────────────
    recommendations: list[Recommendation]
    reasoning: Optional[str]
    confidence: Optional[float]
    follow_up_question: Optional[str]           # If conf < threshold
    follow_up_turn_count: int                   # Default 0

    # ─── Diagnostic ────────────────────────────────────────
    errors: list[str]
    trace: list[dict]
```

### 7.2 Full LangGraph specification

```
                          ┌──────────────────┐
                          │      START       │
                          └────────┬─────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Node: check_user_history       │
                  │  ─────────────────────────────  │
                  │  If user_id is None or          │
                  │  history.review_count < 3:      │
                  │     is_cold_start = True        │
                  └────────────────┬───────────────┘
                                   │
                                   ▼
                  ╔═══════════════════════════════╗
                  ║  CONDITIONAL EDGE              ║
                  ║  cold_start_or_normal          ║
                  ╚═══════════════════════════════╝
                                   │
            ┌──────────────────────┴──────────────────────┐
            │                                              │
       cold_start = True                            cold_start = False
            │                                              │
            ▼                                              ▼
  ┌─────────────────────────────┐         ┌────────────────────────────┐
  │  Node: cold_start_turn       │         │  Node: load_history         │
  │  ──────────────────────────  │         │  Tool: load_user_history    │
  │  Skill: ColdStart            │         └─────────────┬──────────────┘
  │         Bootstrapper         │                       │
  │  Tool: cold_start_interview  │                       ▼
  │                              │         ┌────────────────────────────┐
  │  Sets: cold_start_persona    │         │  Node: build_fingerprint    │
  │        (incomplete or full), │         └─────────────┬──────────────┘
  │        follow_up_question    │                       │
  └──────────────┬───────────────┘                       ▼
                 │                         ┌────────────────────────────┐
                 │                         │  Node: detect_region        │
       persona complete?                   └─────────────┬──────────────┘
                 │                                       │
        ┌────────┴────────┐                              │
        │                 │                              │
        ▼                 ▼                              │
       No                Yes                             │
   (return follow_up                                     │
    question, END)                                       │
        │                 │                              │
        ▼                 │                              │
     ┌─────┐              │                              │
     │ END │              │                              │
     └─────┘              │                              │
                          ▼                              │
            ┌────────────────────────────┐               │
            │  Node: bootstrap_fingerprint│               │
            │  Skill: FingerprintBuilder  │               │
            │  .build_from_persona()      │               │
            │  Sets low-confidence        │               │
            │  fingerprint                │               │
            └─────────────┬──────────────┘               │
                          │                              │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                          ┌────────────────────────────┐
                          │  Node: retrieve_candidates  │
                          │  ─────────────────────────  │
                          │  Tool: retrieve_candidates_ │
                          │        hybrid               │
                          │  Sets: candidate_pool (20)  │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Node: rerank               │
                          │  ─────────────────────────  │
                          │  Tool: rerank_candidates    │
                          │  LLM: Sonnet 4              │
                          │  Sets: reranked_candidates  │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Node: diversity_check      │
                          │  ─────────────────────────  │
                          │  Tool: diversity_check      │
                          │  May reorder reranked       │
                          │  Sets: diversity_score      │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Node: apply_taxonomy_batch │
                          │  Mutates: each top-5 item   │
                          │  to add nigerian_category   │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Node: generate_            │
                          │        explanations         │
                          │  ─────────────────────────  │
                          │  LLM: Sonnet 4              │
                          │  Naija Vibe Mode affects    │
                          │  tone (heavier Pidgin       │
                          │  when active)               │
                          │  Sets: recommendations,     │
                          │        reasoning            │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Node: compute_confidence   │
                          │  Composite signal —         │
                          │  see §7.4                   │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ╔════════════════════════════╗
                          ║  CONDITIONAL EDGE           ║
                          ║  confidence_gate            ║
                          ╚════════════════════════════╝
                                        │
                          ┌─────────────┴──────────────┐
                          │                            │
                  confidence ≥ 0.75            confidence < 0.75
                  OR follow_up_turn ≥ 1        AND follow_up_turn < 1
                          │                            │
                          ▼                            ▼
              ┌───────────────────┐       ┌────────────────────────┐
              │ Node: finalise    │       │ Node: gen_clarifying_  │
              │ Returns final     │       │       question         │
              │ recommendations   │       │ LLM: Haiku             │
              └─────────┬─────────┘       │ Sets: follow_up_       │
                        │                 │       question         │
                        ▼                 │ Increments turn count  │
                      ┌─────┐             └──────────┬─────────────┘
                      │ END │                        │
                      └─────┘                  return to caller
                                               (multi-turn)
```

### 7.3 Cold-start sub-loop

The cold-start branch is itself multi-turn. The graph does NOT loop internally for cold-start; instead, when `cold_start_persona.turns_completed < 3`, the node returns the next agent utterance as `follow_up_question`, and the API returns it to the client. The client's next request includes the updated `conversation_history`, and the graph runs again from `cold_start_turn`.

This means each cold-start exchange is one graph invocation, not one continuous run. This is essential for streaming and statelessness.

### 7.4 Confidence computation

```python
def compute_confidence(state: TaskBState) -> float:
    fingerprint = state["fingerprint"]

    # History sufficiency: 0.0 to 1.0
    history_factor = (
        0.3 if state["is_cold_start"]
        else min(1.0, fingerprint.review_count_at_computation / 20.0)
    )

    # Alignment quality: mean of top-5 alignment_scores
    alignment_factor = mean(rc.alignment_score for rc in state["reranked_candidates"][:5])

    # Diversity: state["diversity_score"]
    diversity_factor = state["diversity_score"]

    # Query specificity: longer queries are usually more specific
    query_factor = min(1.0, len(state["context_query"].split()) / 10.0)

    return round(
        0.35 * history_factor
        + 0.35 * alignment_factor
        + 0.15 * diversity_factor
        + 0.15 * query_factor,
        2,
    )
```

### 7.5 Failure & fallback paths

| Failure | Detection | Recovery |
|---|---|---|
| Empty candidate pool from retrieval | `len(candidate_pool) == 0` | Fall back to BM25-only with relaxed category filter; if still empty, return error |
| Rerank LLM returns invalid JSON | `json.JSONDecodeError` | Retry once with stricter system prompt; if still bad, use BM25 ordering of top-20 |
| Diversity check can't reach 0.6 | No valid swaps | Accept lower diversity, log warning, set diversity_score to actual value |
| Explanation generation fails | LLM exception | Retry; if still fails, return recommendations with template explanations and lower confidence |
| Cold-start parse fails (user gave nonsense) | Skill returns ambiguous persona | Generate a clarifying re-ask for that turn, do not advance turn counter |

---

## 8. Naija Vibe Mode — Full Specification

This section is the single source of truth for how the toggle propagates.

### 8.1 Where the toggle lives

- **In the API request** as a top-level boolean: `naija_vibe_mode: bool` (default `False`)
- **In the state schema** of both `TaskAState` and `TaskBState`
- **In skill APIs** that need to behave differently: `NaijaVibeChecker.score(mode=...)`, `PersonaAuthor.author(intensity=...)`

### 8.2 What changes when it's ON

**In Task A:**
- The Vibe Checker runs in `active` mode (still computes the same score, but the `scored_in_mode` field is `"active"`).
- The conditional edge after `vibe_check` is allowed to route to `plan_regeneration` if score < 0.70.
- `PersonaAuthor` uses `intensity="amplified"` if `retry_count > 0`, which:
  - Increases Pidgin instruction strength in the persona block
  - Selects few-shots from the heavier-register end of the phrase library
  - Adds explicit "use Pidgin where natural" instruction
- The generated review is more likely to contain Pidgin/loanwords if the user's fingerprint supports it (we don't force Pidgin onto users with low slang_index — we just allow the system to push to the upper end of their natural range).

**In Task B:**
- The `generate_explanations` node uses a different prompt template that explicitly invites Nigerian-register explanation style ("write like a knowledgeable Naija friend explaining this to a mate").
- The output explanations are noticeably more Pidgin-flavoured.
- Vibe Checker can also run over the explanations to score them (passive in v1, possibly active in v2 if time permits).

### 8.3 What changes when it's OFF

**In both agents:**
- Vibe Checker runs in `passive` mode — it still computes and reports the Abeg score in the output metadata, but the graph never routes to regeneration based on it.
- `PersonaAuthor` uses `intensity="natural"` — the persona block is built strictly from the fingerprint without amplification.
- `generate_explanations` uses the neutral-tone prompt template.

### 8.4 The crucial property: passive Vibe Checker still scores

Even with Vibe Mode off, we still run the Vibe Checker in passive mode on every output. This gives us:

1. Transparency — users can see the Abeg score on every output and decide if they want to flip the toggle.
2. Evaluation data — the harness can compare passive vs active Abeg distributions, which becomes the **"Vibe Mode On vs Off"** ablation result.
3. No surprises — flipping the toggle isn't a black box; users have seen the score that would have triggered regeneration.

### 8.5 UI contract

The frontend renders the toggle prominently. When activated, an info-tooltip explains: *"Naija Vibe Mode amplifies the Nigerian register of your output. The agent will rewrite up to 2 times if cultural authenticity is low."*

The frontend also always shows the Abeg score, regardless of mode. Below the score, a small label says either "Vibe Mode active — guaranteed ≥ 0.70" or "Vibe Mode off — score is informational".

---

## 9. Prompt Architecture

All prompts are Jinja templates in `naijareview/llm/prompts/`. Templates are loaded once at startup and rendered per request. We document the segment structure of each.

### 9.1 Context window structure — Task A generation

```
SEGMENT 1: System Role         ~50 tokens
SEGMENT 2: User Fingerprint    ~150 tokens
SEGMENT 3: Region Context      ~80 tokens
SEGMENT 4: Item Metadata       ~100 tokens
SEGMENT 5: Item Analysis       ~80 tokens
SEGMENT 6: Few-Shot Examples   ~300 tokens (3 × ~100)
SEGMENT 7: Persona Block       ~100 tokens
SEGMENT 8: Regen Hint          ~50 tokens (only on retries)
SEGMENT 9: Generation Instr.   ~50 tokens
─────────────────────────────────────────────
Target total: ~960 tokens | Hard ceiling: 1200
```

### 9.2 Task A generation prompt (canonical template)

```jinja
SYSTEM:
You are a Nigerian review generation agent. You write reviews that sound
authentically Nigerian — not generic AI text. Match the user's documented
style; do not over-Pidginise users who write formal English.

USER FINGERPRINT:
- Generosity: {{ generosity }} (0=harsh, 1=very generous)
- Verbosity: {{ verbosity_word_range[0] }}–{{ verbosity_word_range[1] }} words typical
- Emotional style: {{ emotional_style }}
- Always mentions: {{ topic_focus | join(", ") }}
- Naija Slang Index: {{ slang_index }} (0=formal English, 1=heavy Pidgin)
- Rating-text consistency: {{ consistency_score }}

REGION: {{ region }} (confidence {{ region_confidence }})
{% if region != "Unknown" %}
Regional markers a {{ region }} reviewer might use: {{ regional_markers | join(", ") }}
{% endif %}

ITEM TO REVIEW:
Name: {{ item.name }}
Category: {{ item.category }} ({{ item.nigerian_category }} in Nigerian taxonomy)
Attributes: {{ item.attributes }}

PREDICTED FIT:
Likely sentiment based on history: {{ inferred_sentiment }}
Predicted rating range: {{ predicted_rating_range }}

AUTHENTIC NIGERIAN REVIEW EXAMPLES:
1. "{{ few_shot_1 }}"
2. "{{ few_shot_2 }}"
3. "{{ few_shot_3 }}"

PERSONA INSTRUCTION:
{{ persona_block }}

{% if regen_hint %}
REGENERATION GUIDANCE (previous attempt scored low):
{{ regen_hint }}
{% endif %}

OUTPUT FORMAT:
Return JSON only:
{
  "review": "<the review text>",
  "rating": <number 1.0 to 5.0>
}
```

### 9.3 Task B reranking prompt (canonical template)

```jinja
SYSTEM:
You are a Nigerian recommendation agent. You reason carefully before
recommending — considering what this user truly wants right now, not just
what is statistically popular.

USER PROFILE:
{{ fingerprint_summary }}
Region: {{ region }}
Current need: {{ context_query }}

CANDIDATES (top-20 from hybrid retrieval):
{% for cand in candidates %}
[{{ loop.index }}] {{ cand.name }} ({{ cand.nigerian_category or cand.category }})
    Rating: {{ cand.avg_rating }} | Reviews: {{ cand.review_count }}
    {{ cand.description | truncate(80) }}
{% endfor %}

REASONING TASK:
For each candidate, score 0–1 on:
- Match to current need ({{ context_query }})
- Fit with user's fingerprint dimensions
- Price/value match given generosity score
- Nigerian-specific signals (parking, area, power, safety) where relevant

Re-rank from 1 to 20. Output JSON only:
{
  "rankings": [
    {"item_index": <1-20>, "rank": <new rank>, "alignment_score": <0-1>,
     "reasoning_snippet": "<one sentence>"},
    ...
  ],
  "overall_confidence": <0-1>
}
```

### 9.4 Task B explanation prompt — TWO templates

**Template A — Neutral (Vibe Mode OFF):**

```jinja
For each top-5 recommended item, write a brief, friendly explanation
(2–3 sentences) of why it suits this user. Use natural English with
occasional Nigerian context where relevant (e.g. mentioning Lagos
traffic if the user is in Lagos). Do not force Pidgin.

User profile: {{ fingerprint_summary }}
Region: {{ region }}
Items: {{ top_5_with_alignment }}
...
```

**Template B — Naija Vibe Active:**

```jinja
You are explaining these recommendations to a Nigerian friend. Write each
explanation (2–3 sentences) in conversational Naija register — Pidgin where
natural, English where needed, with cultural context the user will recognise.

Examples of the tone:
- "Omo, this place go fit your vibe — taste correct, no wahala with price."
- "This one good for chilled evening, no noise, no crowd."

User profile: {{ fingerprint_summary }}
Region: {{ region }}
Items: {{ top_5_with_alignment }}
...
```

### 9.5 Cold-start turn prompts

Three separate Jinja templates (`cold_start_turn_1.jinja`, `_turn_2.jinja`, `_turn_3.jinja`), each runs on Haiku. They are deterministic enough that we can hand-author the agent utterances and use the LLM only to parse the user's response into structured fields.

---

## 10. Memory Engineering — Three Tiers

### 10.1 Episodic Memory (ChromaDB)

- **What:** Raw review history as vector embeddings.
- **Where:** ChromaDB persistent collection per user (or single collection partitioned by `user_id` metadata — TBD by Aaliyah based on perf testing).
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fast, multilingual-ish).
- **Indexed fields:** `text` embedding + metadata (`user_id`, `item_id`, `stars`, `item_category`, `timestamp`).
- **Read patterns:**
  - `load_user_history(user_id)` — fetch all reviews for a user
  - `retrieve_similar(user_id, query_embedding, k)` — semantic search within a user's history (used for context-aware Task A: "what did this user say about similar items?")
- **Write patterns:** Append-only. New reviews added on demo interaction; bulk-loaded from Yelp at data prep.

### 10.2 Semantic Memory (Fingerprint Cache)

- **What:** The compressed 7-dimensional fingerprint per user.
- **Where:** Redis (production), in-memory dict (development).
- **Key:** `fingerprint:{user_id}`
- **Value:** Serialised `Fingerprint` Pydantic model + a `cache_key` field set to `(user_id, last_review_timestamp)`.
- **Read patterns:** `FingerprintBuilder.get_or_build(user_id)` — return cached if `cache_key` matches current state; else recompute.
- **Write patterns:** Computed on first request, recomputed when episodic memory gains a new review (cache invalidated by `save_review`).
- **Eviction:** TTL of 24 hours; on miss, recomputed.

### 10.3 Working Memory (Context Window)

- **What:** The assembled prompt for a single LLM call.
- **Where:** Built fresh in `ContextWindowAssembler` for each generation.
- **Composition:** Documented in §9 — segments are added in order, with token budgeting.
- **Persistence:** None. Discarded after the LLM call.

### 10.4 The cold-start bootstrap loop

For new users, the conversation IS the semantic memory creation step. The flow:

```
Turn 1 user response → parsed → cold_start_persona.food_preference
Turn 2 user response → parsed → cold_start_persona.value_orientation
Turn 3 user response → parsed → cold_start_persona.atmosphere + budget
                              ↓
              FingerprintBuilder.build_from_persona()
                              ↓
              Low-confidence Fingerprint written to cache
                              ↓
              Agent B proceeds with normal retrieval flow
```

The fingerprint built from a cold-start persona has all confidence intervals set wide (e.g. `generosity_score: 0.5 ± 0.4`) because we have no behavioural evidence. As the user provides feedback or makes selections, the fingerprint is updated.

---

## 11. LLM Orchestration

### 11.1 The router

```python
# llm/router.py

class LLMRouter:
    def __init__(self):
        self.sonnet = AnthropicClient(model="claude-sonnet-4-20250514")
        self.haiku = AnthropicClient(model="claude-haiku-4-5-20251001")

    def call(self, tier: Literal["generation","utility"],
             prompt: str, max_tokens: int = 1000,
             temperature: float = 0.7) -> str:
        client = self.sonnet if tier == "generation" else self.haiku
        return client.complete(prompt, max_tokens=max_tokens, temperature=temperature)

    def call_with_retry(self, tier, prompt, max_tokens=1000,
                        temperature=0.7, max_retries=2) -> str:
        for attempt in range(max_retries + 1):
            try:
                return self.call(tier, prompt, max_tokens, temperature)
            except RateLimitError as e:
                if attempt < max_retries:
                    sleep(2 ** attempt)
                    continue
                raise
            except APIError as e:
                if attempt < max_retries:
                    continue
                raise
```

### 11.2 Routing rules

| Task | Tier | Rationale |
|---|---|---|
| `analyse_item_for_user` | Utility (Haiku) | Short structured analysis; cost-sensitive (runs every request) |
| `generate_review_draft` (Task A) | Generation (Sonnet) | Quality-critical; the output is the deliverable |
| Vibe Check LLM-judged components | Utility (Haiku) | Runs on every output |
| `rerank_candidates` (Task B) | Generation (Sonnet) | Quality-critical; chain-of-thought reasoning |
| `generate_explanations` (Task B) | Generation (Sonnet) | User-facing copy quality matters |
| `cold_start_interview` | Utility (Haiku) | Structured parsing only |
| `gen_clarifying_question` | Utility (Haiku) | Short, low-stakes |

### 11.3 Cost projection

If we generate 100 reviews and 100 recommendations across all ablations and the harness:

- Sonnet generation calls: ~200 × 1k tokens in + 500 tokens out = ~300k tokens
- Haiku utility calls: ~600 × 500 tokens in + 200 tokens out = ~420k tokens

Well within hackathon budget. The cost discipline matters more for the synthetic corpus generation (1000 reviews × Sonnet = ~500k tokens) — Shiloh and Testimony should coordinate so we don't blow through credits on iteration.

---

## 12. Evaluation Harness Internals

### 12.1 Entry point

```python
# eval/harness.py

class EvalHarness:
    def __init__(self, config: HarnessConfig):
        self.config = config

    def run_task_a(self, variant: str = "full") -> TaskAResults:
        """Generate reviews for held-out users, score against ground truth."""

    def run_task_b(self, variant: str = "full") -> TaskBResults:
        """Recommend items for held-out users, score against actual reviews."""

    def run_ablation_sweep(self) -> AblationReport:
        """Run all 5 variants and produce comparison table."""
```

### 12.2 Held-out construction

- Take 20% of Yelp users with ≥ 5 reviews
- For each held-out user: mask their last 3 reviews
- Eval set: ~1000 (user, masked review) pairs for Task A
- For Task B: same 20%, query is constructed from the masked review's item category

### 12.3 Metrics

| Metric | Where computed | Library |
|---|---|---|
| ROUGE-L | Task A | `rouge-score` |
| BERTScore | Task A | `bert-score` |
| NDCG@10 | Task B | `sklearn.metrics.ndcg_score` |
| Hit@10 | Task B | Custom (item_id in top-10?) |
| Abeg Score | Task A + B | Our `NaijaVibeChecker` in passive mode |
| Rating MAE | Task A | Custom (|pred − actual|) |

### 12.4 Variant toggles

```python
class HarnessConfig:
    variant: Literal["full","vibe_off","no_fingerprint","no_persona","no_synthetic"]
    sample_size: int = 1000
    seed: int = 42

# Each variant flips one switch in the agent construction
def build_agent_for_variant(variant: str) -> CompiledStateGraph:
    if variant == "no_fingerprint":
        # Replace FingerprintBuilder with one that returns average-user fingerprint
        ...
    if variant == "no_persona":
        # Strip AfriSenti few-shots and region detection
        ...
    # etc.
```

### 12.5 Output format

```
results/
├── 2026-05-18_full.json
├── 2026-05-18_vibe_off.json
├── ...
└── ablation_comparison.csv
```

Each JSON contains:
- Per-sample scores
- Aggregate means and std devs
- Failure counts
- Run metadata (variant, seed, timestamp, git SHA)

---

## 13. API Contracts

### 13.1 `POST /task-a/generate`

**Request:**
```json
{
  "user_id": "string",
  "item": {
    "item_id": "string",
    "name": "string",
    "category": "string",
    "attributes": {},
    "avg_rating": 0.0,
    "review_count": 0,
    "description": "string"
  },
  "naija_vibe_mode": false
}
```

**Response (200):**
```json
{
  "generated_review": "string",
  "predicted_rating": 4.2,
  "confidence": 0.87,
  "fingerprint_match": "string",
  "style_notes": "string",
  "abeg_score": 0.78,
  "vibe_breakdown": {
    "nigerian_authenticity": 0.82,
    "cultural_accuracy": 0.75,
    "persona_consistency": 0.81
  },
  "naija_vibe_mode_active": false,
  "retry_count": 0,
  "trace": [
    {"node": "load_history", "duration_ms": 12, "status": "ok"},
    ...
  ]
}
```

**Error (404):**
```json
{"error": "user_not_found", "user_id": "string"}
```

### 13.2 `POST /task-b/recommend`

**Request:**
```json
{
  "user_id": "string | null",
  "context_query": "string",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "agent", "content": "..."}
  ],
  "naija_vibe_mode": false
}
```

**Response (200) — final recommendations:**
```json
{
  "recommendations": [
    {
      "item": {...},
      "rank": 1,
      "explanation": "string",
      "alignment_dimensions": ["value", "ambience"]
    },
    ...
  ],
  "reasoning": "string",
  "confidence": 0.91,
  "cold_start_mode": false,
  "diversity_score": 0.76,
  "follow_up_question": null,
  "naija_vibe_mode_active": false
}
```

**Response (200) — needs more turns (cold-start or clarification):**
```json
{
  "recommendations": [],
  "reasoning": null,
  "confidence": null,
  "cold_start_mode": true,
  "follow_up_question": "Omo, welcome! Quick one — what kind of food do you normally enjoy?",
  "naija_vibe_mode_active": false
}
```

### 13.3 Admin endpoints (development only)

- `GET /healthz` — basic health
- `GET /admin/index-stats` — Chroma + FAISS counts
- `POST /admin/rebuild-fingerprint/{user_id}` — force recompute

---

## 14. Observability, Error Handling, Fallbacks

### 14.1 Trace logging

Every node appends to `state["trace"]`:

```python
state["trace"].append({
    "node": "build_fingerprint",
    "started_at": ts,
    "duration_ms": elapsed,
    "status": "ok",  # or "error"
    "summary": "Fingerprint computed from 47 reviews"
})
```

The full trace is returned in the API response (in dev) and logged structurally (in prod). The UI's reasoning-trace display renders this directly.

### 14.2 Structured logging

Use `structlog`. Every log line includes:
- `request_id` (generated by middleware)
- `user_id` (if known)
- `agent` (task_a / task_b)
- `node` (current node)
- `level`

### 14.3 Error taxonomy

| Error class | Where | Handling |
|---|---|---|
| `UserNotFoundError` | episodic memory | Task A: return error response; Task B: route to cold-start |
| `InsufficientHistoryError` | fingerprint | Task A: proceed with low-confidence fingerprint; Task B: route to cold-start |
| `LLMRateLimitError` | router | Retry with backoff (2 attempts); then fail with 503 |
| `LLMAPIError` (other) | router | Retry once; then fall back to template output and lower confidence |
| `RetrievalEmptyError` | retrieval | Task B: relax filters and retry; if still empty, return empty recommendations with error |
| `VibeScorerError` | vibe checker | Compute lexical components only; mark LLM components as 0.5 |

### 14.4 Fallback principle

**A failed component degrades gracefully — it does not crash the request.** Every node has a fallback that produces a usable but lower-confidence output. The confidence score is the user-facing signal that something went imperfectly.

---

## 15. Open Questions

These are decisions deferred until we have more data:

1. **ChromaDB collection layout.** One collection per user vs single collection partitioned by `user_id`. Decision driven by Aaliyah's perf testing on Day 2.
2. **Synthetic corpus size.** Target is 500–1000 but depends on Sonnet rate limits and how many pass Abeg ≥ 0.75. Shiloh + Testimony aligned on Day 4.
3. **User-study scoring rubric exact wording.** Shiloh drafts by Day 5, all three review.
4. **Whether to expose the trace in production responses.** Currently yes in dev; for the public demo URL we may want a `?trace=true` query parameter to opt-in.
5. **Cross-domain evaluation specifics.** Task B says "cross-domain" but how aggressively we mix Amazon ↔ Yelp candidates is a design call. Aaliyah owns.
6. **Frontend state management.** React `useState` is probably enough but Zustand may be cleaner for the cold-start conversation state. Aaliyah's call.

---

## Appendix A: Component Ownership Cross-Reference

For quick lookup — which teammate owns which component (full detail in TASK_SPLIT.md):

| Component | Owner |
|---|---|
| Tool registry implementations | Testimony |
| `FingerprintBuilder` skill | Testimony |
| `RegionInferenceEngine` skill | Testimony |
| `NaijaVibeChecker` skill | Testimony |
| `PersonaAuthor` skill | Testimony |
| `ContextWindowAssembler` skill | Testimony |
| `RegenerationStrategist` skill | Testimony |
| Agent A graph | Testimony |
| Agent B graph | Aaliyah |
| `ColdStartBootstrapper` skill | Aaliyah |
| Retrieval stack (Chroma + FAISS) | Aaliyah |
| FastAPI + Docker | Aaliyah |
| Eval harness | Aaliyah |
| Frontend React UI | Testimony|
| Dataset curation + EDA | Shiloh |
| Phrase library + Pidgin mapper | Shiloh |
| Synthetic corpus generation pipeline | Shiloh + Testimony |
| Taxonomy YAML | Shiloh |
| User study | Shiloh |
| Solution paper | Shiloh |

---

*NaijaReview Intelligence | Internal Engineering Architecture v2.0 | 13 May 2026*