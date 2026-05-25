# Naiview Intelligence — Dataset Strategy & Sources

**DSN × BCT LLM Agent Challenge 3.0 · Team Panthers**  
**Version:** 1.0 · May 2026

---

## 1. Strategy Overview

The dataset strategy follows a three-layer architecture designed to solve a core problem: **no large-scale, labelled Nigerian review dataset exists**.

| Layer | Source type | Purpose |
|-------|------------|---------|
| **Backbone** | Yelp + Amazon reviews | Volume, review structure, rating patterns |
| **Calibration** | AfriSenti + Nigerian corpora | Cultural signal injection |
| **Augmentation** | Synthetic generation | Nigerian-style review coverage |

The three layers are merged into a single integrated dataset: `integrated_final_dataset_50k_v2.jsonl` — 52,002 records.

---

## 2. Layer 1 — Backbone (Yelp + Amazon)

### 2.1 Yelp Open Dataset

- **Source:** Yelp Academic Dataset (publicly available)
- **Records used:** ~40,000 reviews (filtered from 7M+)
- **Filter criteria:**
  - Reviews ≥ 50 words
  - Users with ≥ 5 reviews (fingerprint computability)
  - Categories remapped to Nigerian taxonomy (see §5)
- **Fields:** `user_id, business_id, stars, text, date, useful, funny, cool`
- **Role in system:** Primary source for user history, fingerprint computation, and held-out evaluation

### 2.2 Amazon Review Dataset

- **Source:** Amazon Product Reviews (McAuley et al., 2023 release)
- **Records used:** ~8,000 reviews (electronics, books, beauty)
- **Filter criteria:**
  - Verified purchase only
  - Rating variance ≥ 1 across user's review history
  - English text (langdetect confirmed)
- **Role in system:** Product/item review diversity; supplement for non-food categories

### 2.3 Why Western data?

Nigerian-specific datasets with sufficient volume for fingerprinting (≥5 reviews per user) do not exist publicly. Yelp and Amazon provide:
- Statistical volume for fingerprint reliability
- Diverse category coverage
- Temporal metadata for recency weighting

The cultural signal is injected at the model layer (NLM, Vibe Checker) and calibration layer (AfriSenti), not assumed from the data.

---

## 3. Layer 2 — Calibration (AfriSenti + Nigerian Corpora)

### 3.1 AfriSenti

- **Source:** AfriSenti-SemEval Shared Task 12 (Muhammad et al., 2023)
- **Languages used:** Nigerian Pidgin English (`pcm`), Yoruba (`yo`), Hausa (`ha`), Igbo (`ig`)
- **Records:** ~4,000 sentiment-labelled tweets and short texts
- **Role:**
  - Calibrates VADER sentiment scores (which were trained on American English)
  - Validates Naija Slang Index phrase library coverage
  - Provides authentic Pidgin intensifier patterns for the PhraseLibrary

### 3.2 NaijaSenti

- **Source:** NaijaSenti corpus (Taiwo & Azeez, 2022)
- **Records:** ~1,200 product and service reviews in Nigerian English/Pidgin
- **Role:**
  - Gold standard for Naija Vibe Checker calibration
  - Few-shot examples in ChromaDB (highest-authenticity examples selected manually)
  - Used to validate Abeg Score threshold (0.70 cutoff selected to match human preference)

### 3.3 Regional marker extraction

Regional markers for the 6 supported regions were extracted from:
- Social media scrapes (Twitter/X, Nairaland) — keyword + region co-occurrence
- Manual annotation by team members (native speakers from Kano, Lagos, Enugu, Port Harcourt)

| Region | Example markers |
|--------|----------------|
| Lagos | "omo", "e go be", "VI", "Lekki", "Third Mainland" |
| Abuja | "magu", "wuse", "gwarinpa", "abuja price" |
| Kano | "wallahi", "dan", "suya na asali" |
| Enugu | "nna", "ofe onugbu", "nine-nine" |
| Port Harcourt | "naija boy", "warri side", "bonny light" |
| Ibadan | "omo ale", "dugbe", "bode" |

---

## 4. Layer 3 — Synthetic Augmentation

### 4.1 Motivation

The backbone has insufficient naija-tagged users (only 2/30 in the held-out set). Synthetic augmentation addresses this by generating labelled Nigerian-style reviews to:
- Balance naija vs non-naija examples in few-shot retrieval
- Provide ChromaDB population for cold-start bootstrapping
- Cover Nigerian-specific item categories absent from Yelp/Amazon

### 4.2 Generation method

Synthetic reviews generated using Gemini 2.5 Pro with:
- Explicit Naija Slang Index targets (0.3, 0.6, 0.9)
- Region specified
- Category from Nigerian taxonomy
- Minimum Abeg Score 0.75 (auto-filtered — lower scoring outputs discarded)

**Volume:** ~3,500 synthetic Nigerian reviews generated; ~2,800 passed the Abeg ≥ 0.75 threshold.

### 4.3 Synthetic data policy

Synthetic records are:
- Flagged with `synthetic: true` in the dataset
- Excluded from evaluation held-out sets (eval uses real Yelp users only)
- Used only for ChromaDB population and few-shot retrieval
- Not counted toward ROUGE-L or BERTScore computation

---

## 5. Nigerian Taxonomy Mapping

Standard Yelp/Amazon categories were remapped to Nigerian-context equivalents:

| Source category | Nigerian taxonomy | Notes |
|----------------|-----------------|-------|
| Restaurants → Nigerian Cuisine | Food & Drink · Local | Jollof, suya, pepper soup |
| Restaurants → American/Fast Food | Food & Drink · Western | KFC, Chicken Republic |
| Shopping → Electronics | Tech & Gadgets | Phones dominant |
| Shopping → Grocery | Market / Shopping | Open markets |
| Auto → Repair Shops | Mechanic / Auto | Roadside mechanic culture |
| Health → Clinics | Healthcare | PHC, private clinics |
| Education → Tutoring | School / Training | JAMB, WAEC prep |
| Hotels | Hotels & Travel | Lagos corridor heavy |
| Nightlife → Bars/Clubs | Entertainment / Nightlife | Afrobeats context |
| Beauty → Salons | Salon & Spa | Hair braiding culture |

Mapping defined in `data/taxonomy.yaml`. Unmapped categories fall back to `General`.

---

## 6. Integrated Dataset Schema

Each record in `integrated_final_dataset_50k_v2.jsonl`:

```json
{
  "user_id": "string",
  "item_id": "string",
  "review_text": "string",
  "stars": 1.0–5.0,
  "date": "YYYY-MM-DD",
  "category": "string (Nigerian taxonomy)",
  "source": "yelp | amazon | afrisenti | synthetic",
  "naija_tagged": true | false,
  "region": "Lagos | Abuja | Kano | Enugu | Port Harcourt | Ibadan | Unknown",
  "word_count": integer,
  "synthetic": true | false
}
```

---

## 7. Held-out Evaluation Construction

- **Eligible users:** ≥5 reviews in dataset → 575 users from 52,002 records
- **Masking:** Last review by date is held out as the eval target
- **Remaining reviews:** Form the user's history as seen by the agent
- **Sample:** 30 users drawn at seed=42
- **Synthetic exclusion:** Synthetic records are not eligible for held-out selection

---

## 8. Data Volume Summary

| Source | Records | Naija-tagged | In eval? |
|--------|---------|-------------|---------|
| Yelp (filtered) | ~40,000 | ~2,800 | Yes |
| Amazon (filtered) | ~8,000 | ~200 | Yes |
| AfriSenti | ~4,000 | 4,000 | No (calibration only) |
| NaijaSenti | ~1,200 | 1,200 | No (ChromaDB few-shots) |
| Synthetic | ~2,800 | 2,800 | No |
| **Total integrated** | **52,002** | **~5,600** | — |

---

*NaijaReview Intelligence v0.1.0 · DSN × BCT Hackathon 3.0 · Team Panthers*
