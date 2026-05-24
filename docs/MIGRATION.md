"""
CODEBASE MIGRATION GUIDE — NaijaReview Intelligence
=====================================================
What changed in the data pipeline and what needs to change in the codebase.

Summary of changes:
  1. ChromaDB: PersistentClient → HttpClient (Railway)
  2. ChromaDB: user_personas collection (NEW) replaces naijareview_reviews
  3. FAISS: bge-m3 (1024-dim) → bge-base-en-v1.5 (768-dim)
  4. FAISS metadata: JSON list format → JSON dict format (needs adapter)
  5. Embedding model: bge-m3 → bge-base-en-v1.5
  6. User ID removed from frontend → describe-persona path only
"""

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 1: config.py — Add Railway ChromaDB settings
# ═══════════════════════════════════════════════════════════════════════════════
"""
CHANGE in naijareview/config.py:

Replace:
    # ─── ChromaDB ─────────────────────────────────
    chroma_persist_dir: Path = Path("./data/chroma")
    chroma_collection_prefix: str = "naijareview"

    # ─── FAISS ────────────────────────────────────
    faiss_index_path: Path = Path("./data/processed/faiss_index")
    embedding_model: str = "BAAI/bge-m3"

With:
    # ─── ChromaDB (Railway) ───────────────────────
    chroma_host: str = "chromadb-production-9e98.up.railway.app"
    chroma_port: int = 443
    chroma_ssl: bool = True
    chroma_auth_token: str = Field("", description="ChromaDB auth token for Railway")
    chroma_collection_prefix: str = "naijareview"
    # Legacy local path — kept for fallback / dev mode
    chroma_persist_dir: Path = Path("./data/chroma")
    chroma_mode: Literal["railway", "local"] = "railway"

    # ─── FAISS ────────────────────────────────────
    faiss_index_path: Path = Path("./data/processed/faiss_index_bge_opt")
    embedding_model: str = "BAAI/bge-base-en-v1.5"

Add to .env:
    CHROMA_HOST=chromadb-production-9e98.up.railway.app
    CHROMA_PORT=443
    CHROMA_SSL=true
    CHROMA_AUTH_TOKEN=f36010b18e1d5f899383d172f176bfc0f74649febce450a6e123eb71b05ecfad
    CHROMA_MODE=railway
    FAISS_INDEX_PATH=./data/processed/faiss_index_bge_opt
    EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 2: memory/episodic.py — Switch ChromaDB to HttpClient
# ═══════════════════════════════════════════════════════════════════════════════
"""
CHANGE in naijareview/memory/episodic.py:

Replace the _get_collection method:

    def _get_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        import chromadb
        client = chromadb.PersistentClient(path=self.persist_dir)
        ...

With:

    def _get_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        import chromadb
        from naijareview.config import settings

        if settings.chroma_mode == "railway":
            client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                ssl=settings.chroma_ssl,
                headers={"Authorization": f"Bearer {settings.chroma_auth_token}"}
            )
        else:
            client = chromadb.PersistentClient(path=self.persist_dir)

        try:
            self._collection = client.get_collection(self.collection_name)
        except (ValueError, Exception):
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

ALSO: The collection name changes.
    Old: naijareview_reviews  (user review history, partitioned by user_id)
    New: user_personas        (pre-computed persona embeddings)

    The user_personas collection stores:
      - ids:       user_id strings
      - documents: persona description text
      - metadatas: {emotion, rating_tendency, is_nigerian, top_domain,
                    avg_stars, avg_pidgin_density, naija_mode_pct, region,
                    review_count}
      - embeddings: 768-dim bge-base vectors

    This is a DIFFERENT collection schema from the old naijareview_reviews.
    The old collection stored individual reviews partitioned by user_id.
    The new collection stores one record per USER with their persona profile.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 3: memory/item_index.py — Fix FAISS metadata format mismatch
# ═══════════════════════════════════════════════════════════════════════════════
"""
CRITICAL CHANGE in naijareview/memory/item_index.py:

The codebase expects FAISS metadata as a JSON LIST (parallel array):
    [
      {"item_id": "abc", "name": "...", ...},   // index 0
      {"item_id": "def", "name": "...", ...},   // index 1
    ]

But the new faiss_index_bge_opt.json stores it as a JSON DICT:
    {
      "model": "BAAI/bge-base-en-v1.5",
      "dim": 768,
      "total": 27665,
      "item_id_map": {"0": "abc", "1": "def", ...},
      "metadata": {"abc": {...}, "def": {...}, ...}
    }

Replace the _load method:

    def _load(self):
        import faiss
        if not self.index_path.exists():
            self._index = faiss.IndexFlatIP(self._embed_provider.dim())
            self._metadata = []
            return self._index, self._metadata

        self._index = faiss.read_index(str(self.index_path))

        if self.metadata_path.exists():
            raw = json.loads(self.metadata_path.read_text())

            # Handle both old format (list) and new format (dict with item_id_map)
            if isinstance(raw, list):
                # Old format: parallel list
                self._metadata = raw
            elif isinstance(raw, dict) and "item_id_map" in raw:
                # New format: dict with item_id_map and metadata
                item_id_map = raw["item_id_map"]  # {"0": "abc", "1": "def", ...}
                meta_dict   = raw.get("metadata", {})
                # Build parallel list in index order
                self._metadata = []
                for idx in range(len(item_id_map)):
                    iid = item_id_map.get(str(idx), "")
                    meta = meta_dict.get(iid, {"item_id": iid})
                    self._metadata.append(meta)
            else:
                self._metadata = []

        return self._index, self._metadata
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 4: tools/memory.py — Update singleton to support Railway mode
# ═══════════════════════════════════════════════════════════════════════════════
"""
CHANGE in naijareview/tools/memory.py:

The _get_episodic() function creates the EpisodicMemory singleton.
It currently only passes persist_dir. Add support for Railway ChromaDB
by passing the connection mode through.

No code change needed IF you update episodic.py as shown above —
the episodic.py _get_collection() method reads settings.chroma_mode
directly. The tools/memory.py singleton just passes the persist_dir
as a fallback for local mode.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 5: memory/embedding.py — No changes needed
# ═══════════════════════════════════════════════════════════════════════════════
"""
The EmbeddingProvider already supports bge-base-en-v1.5:

    _DIM_MAP = {
        ...
        "BAAI/bge-base-en-v1.5": 768,
        ...
    }

Just change EMBEDDING_MODEL in .env to "BAAI/bge-base-en-v1.5"
and the provider will load the correct model automatically.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 6: tools/retrieval.py — Update FAISS metadata path
# ═══════════════════════════════════════════════════════════════════════════════
"""
CHANGE in naijareview/tools/retrieval.py:

The FAISS index path changes from:
    ./data/processed/faiss_index  →  ./data/processed/faiss_index_bge_opt

This is handled by the config change (FAISS_INDEX_PATH env var).
The metadata sidecar is auto-derived as index_path.with_suffix(".json").

The BM25Index also reads from this metadata file. Since the new metadata
format is a dict (not a list), the BM25Index._load() method needs the
same format adapter as ItemIndex._load():

    def _load(self):
        from rank_bm25 import BM25Okapi

        raw = json.loads(self.metadata_path.read_text())

        # Handle new dict format
        if isinstance(raw, dict) and "metadata" in raw:
            self._metadata = list(raw["metadata"].values())
        elif isinstance(raw, list):
            self._metadata = raw
        else:
            self._metadata = []

        corpus = []
        self._item_ids = []
        for item in self._metadata:
            search_text = item.get("name", "")
            if item.get("description"):
                search_text += " " + item["description"]
            if item.get("category"):
                search_text += " " + item["category"]
            corpus.append(search_text)
            self._item_ids.append(item.get("item_id", ""))

        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self._bm25 = BM25Okapi(tokenized_corpus)
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 7: .env — New environment variables
# ═══════════════════════════════════════════════════════════════════════════════
DOTENV_TEMPLATE = """
# ─── Gemini ───────────────────────────────────
GEMINI_API_KEY=your-gemini-key-here
GEMINI_GENERATION_MODEL=gemini-2.5-pro
GEMINI_UTILITY_MODEL=gemini-2.0-flash

# ─── ChromaDB (Railway) ──────────────────────
CHROMA_HOST=chromadb-production-9e98.up.railway.app
CHROMA_PORT=443
CHROMA_SSL=true
CHROMA_AUTH_TOKEN=f36010b18e1d5f899383d172f176bfc0f74649febce450a6e123eb71b05ecfad
CHROMA_MODE=railway
CHROMA_COLLECTION_PREFIX=naijareview

# ─── FAISS ────────────────────────────────────
FAISS_INDEX_PATH=./data/processed/faiss_index_bge_opt
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# ─── Database ─────────────────────────────────
DATABASE_URL=sqlite:///./data/naijareview.db

# ─── Auth ─────────────────────────────────────
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256

# ─── Cache ────────────────────────────────────
CACHE_BACKEND=memory
"""


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FILES TO DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════
"""
Copy these files from Google Drive to your deployment:

  FROM: /content/drive/MyDrive/NaijaReview_Data/Naiview/data/processed/
  TO:   ./data/processed/

  Required files:
    faiss_index_bge_opt       — 81 MB  (IndexFlatIP, 27,665 items, 768-dim)
    faiss_index_bge_opt.json  — 5.8 MB (metadata dict with item_id_map)

  ChromaDB data is on Railway — no local files needed.
  The user_personas collection (41,783 records) is already uploaded.

  Optional (for enriched item display in UI):
    item_display_metadata.json — if you build it from the Yelp business.json
"""


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY OF ALL CHANGES
# ═══════════════════════════════════════════════════════════════════════════════
"""
File                          Change                              Priority
─────────────────────────────────────────────────────────────────────────────
config.py                     Add chroma_host/port/ssl/token       REQUIRED
                              Change embedding_model to bge-base
                              Change faiss_index_path

memory/episodic.py            _get_collection: HttpClient switch   REQUIRED

memory/item_index.py          _load: handle dict metadata format   REQUIRED

memory/embedding.py           No code change (already supports     NONE
                              bge-base-en-v1.5)

tools/memory.py               No code change (reads from config)   NONE

tools/retrieval.py            BM25Index._load: handle dict format  REQUIRED

.env                          Add CHROMA_HOST/PORT/SSL/TOKEN       REQUIRED
                              Update FAISS_INDEX_PATH
                              Update EMBEDDING_MODEL

ChromaDB collection           user_personas (NEW)                  REQUIRED
                              naijareview_reviews (OLD — unused)

FAISS index                   faiss_index_bge_opt (768-dim)        REQUIRED
                              OLD: faiss_index (1024-dim) — delete
"""