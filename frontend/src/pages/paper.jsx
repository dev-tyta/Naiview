/* PAPER — Solution paper + inline web reader */

const { useState } = React;

const PAPER_SECTIONS = [
  {
    id: "abstract", title: "Abstract",
    content: `Existing review-generation and recommendation systems treat cultural context as a tag, not a feature. We argue Nigerian online behaviour — bimodal ratings, code-switching, regional dialect distributions, hedge-free emotional intensity — requires architecture, not decoration.

Naiview Intelligence is a LangGraph-based two-agent system. Agent A generates culturally-authentic Nigerian product reviews from a 7-dimensional behavioural fingerprint. Agent B produces personalised cross-domain recommendations through hybrid BM25+semantic retrieval and chain-of-thought reranking, with a 3-turn cold-start conversation for new users.

Both agents share a Naija Vibe Checker that scores every output on cultural authenticity, cultural accuracy, and persona consistency (Abeg Score = 0.40×auth + 0.35×acc + 0.25×persona). Active Naija Vibe Mode triggers regeneration when Abeg < 0.70, looping back through the persona-authoring stage up to two times.

Quantitative results: ROUGE-L +35%, BERTScore +13%, NDCG@10 +28%, Naija Vibe Score 0.81 vs 0.32 baseline. In blind human preference testing across 12 native Nigerian speakers, Naija Vibe Mode outputs were preferred 78% of the time.`,
  },
  {
    id: "problem", title: "1. The Problem",
    content: `AI review and recommendation systems trained on Western data mismodel Nigerian users in three specific ways.

(1) Rating distribution mismatch. Nigerian reviewers show a bimodal pattern — 5 stars when satisfied, 1 star when dissatisfied — while Western models expect a Gaussian bell curve centred around 3–4. An AI trained on the bell curve systematically misreads Nigerian preference signals.

(2) Regional identity erasure. A Kano reviewer writing about suya uses completely different vocabulary, sentiment markers, and cultural references than an Enugu reviewer writing about ofe onugbu. Treating both as "Nigerian" without regional specificity loses the signal.

(3) Register flattening. Pidgin English, code-switching, and Nigerian-specific intensifiers ("e sweet die", "no cap", "abeg") carry semantic and emotional content that standard NLP pipelines strip away. A review scoring −0.2 on VADER might be enthusiastic praise written in a Pidgin register that VADER was never trained on.`,
  },
  {
    id: "architecture", title: "2. System Architecture",
    content: `The system comprises two independent LangGraph agents sharing a common infrastructure layer.

Agent A (Review Generation) traverses 12 typed nodes: load_history → build_fingerprint → detect_region → analyse_item → apply_taxonomy → fetch_few_shots → author_persona → assemble_prompt → generate_draft → vibe_check → [finalise | plan_regen → author_persona loop].

The 7-dimensional behavioural fingerprint captures: generosity (mean stars vs platform average), verbosity (quantile rank of word count), emotional intensity (intensifier density), topic focus (top-3 noun phrases via spaCy), consistency (Pearson correlation of sentiment to stars), recency weight (exponential decay coefficient), and Naija slang index (phrase library match fraction).

Agent B (Recommendations) has 14 nodes with two entry paths: existing users follow history → fingerprint → region; new users follow the 3-turn cold-start conversation path, which terminates with a bootstrapped low-confidence fingerprint. Both paths merge at retrieve_candidates, which uses hybrid BM25×0.4 + Semantic×0.6 retrieval over a FAISS flat index with BAAI/bge-m3 embeddings.

Infrastructure: ChromaDB for episodic memory, FAISS for the global item index, Redis for fingerprint caching (24 h TTL), Gemini 2.5 Pro as the generation tier, Gemini 2.0 Flash as the utility tier.`,
  },
  {
    id: "evaluation", title: "3. Evaluation",
    content: `We evaluate across six metrics on a held-out test set of 500 (user, item, review) triples, against a non-culturally-aware baseline (same architecture, standard English prompts, no NLM, no Vibe Checker).

ROUGE-L: 0.42 (+35% vs 0.31 baseline). Lexical overlap with human-written Nigerian reviews improves substantially once the system uses the phrase library and Nigerian register.

BERTScore: 0.78 (+13% vs 0.69). Semantic similarity gain is smaller than lexical — the baseline already captures meaning, but misses cultural expression.

Rating RMSE: 0.61 (−31% vs 0.89 baseline — lower is better). The bimodal-aware fingerprint reduces rating prediction error significantly.

NDCG@10: 0.74 (+28% vs 0.58). The LLM-backed reranker and diversity check improve recommendation ranking quality.

Naija Vibe Score: 0.81 (vs 0.32 baseline). Average Abeg Score across the test set. The 0.32 baseline score confirms that standard generation produces culturally-inauthentic outputs even when prompted with Nigerian context.

Human evaluation (12 native Nigerian speakers, 4 regions, 60 review pairs each): 78% preference for Naija Vibe Mode outputs. Authenticity 0.87, helpfulness 0.81, faithfulness 0.84.`,
  },
  {
    id: "conclusion", title: "4. Conclusion",
    content: `We demonstrated that cultural authenticity in AI-generated content requires architectural commitment, not post-hoc flavouring. The 7-dimensional behavioural fingerprint outperforms persona-description prompting alone. The Naija Vibe Checker's regeneration loop recovers outputs that would otherwise be culturally flat.

The system generalises: the naija_vibe_mode=False path produces standard English outputs using the same fingerprinting and retrieval infrastructure, making it a general-purpose review and recommendation engine that Nigerian cultural mode layers on top of.

Future work: expansion to other African linguistic contexts (Swahili, Amharic), real-time fingerprint updates via streaming review ingestion, and user-controlled vibe intensity (0.0–1.0) rather than binary on/off.

We didn't build a recommendation engine and add Nigerian flavour. We built Nigerian intelligence and gave it an engine.`,
  },
];

function PaperReader({ onClose }) {
  const [activeSection, setActiveSection] = useState("abstract");
  const sec = PAPER_SECTIONS.find(s => s.id === activeSection);

  return (
    <div className="paper-reader-overlay" role="dialog" aria-modal="true" aria-label="Paper reader"
         onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="paper-reader-modal">
        <div className="paper-reader-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow tealtxt" style={{ marginBottom: 6 }}>Solution Paper · Web Edition</div>
            <h2 style={{ fontSize: 'clamp(15px, 2vw, 20px)', letterSpacing: '-0.01em', lineHeight: 1.3 }}>
              Naiview Intelligence: A Culturally-Aware LLM Agent System for Nigerian User Modelling and Recommendation
            </h2>
            <div className="mono dim" style={{ fontSize: 11, marginTop: 6 }}>Testimony · Aaliyah · Shiloh · DSN × BCT 2026</div>
          </div>
          <button onClick={onClose} className="btn btn-sm" aria-label="Close paper reader" style={{ flexShrink: 0 }}>✕ Close</button>
        </div>
        <div className="paper-reader-body">
          <div className="paper-reader-nav" role="tablist">
            {PAPER_SECTIONS.map(s => (
              <button key={s.id} role="tab" aria-selected={activeSection === s.id}
                className="paper-nav-btn"
                onClick={() => setActiveSection(s.id)}
                style={{
                  color: activeSection === s.id ? 'var(--teal)' : 'var(--fg-mute)',
                  borderLeftColor: activeSection === s.id ? 'var(--teal)' : 'transparent',
                  background: activeSection === s.id ? 'var(--teal-soft)' : 'transparent',
                }}>
                {s.title}
              </button>
            ))}
          </div>
          <div className="paper-reader-content" role="tabpanel">
            <h3 style={{ fontSize: 20, marginBottom: 20, color: 'var(--fg)' }}>{sec.title}</h3>
            {sec.content.split('\n\n').map((para, i) => (
              <p key={i} style={{ fontSize: 15, lineHeight: 1.85, color: 'var(--fg-dim)', marginBottom: 20, textWrap: 'pretty' }}>{para}</p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PaperPage({ navigate, vibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? 'pidgin' : 'en'] || {}).paper || {};
  const [readerOpen, setReaderOpen] = useState(false);

  const supps = [
    {
      title: "Technical Architecture Document",
      desc: "Full internal engineering spec — every tool, skill, node, and schema defined.",
      size: "2.4 MB · PDF",
      icon: (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>),
    },
    {
      title: "Dataset Strategy & Sources",
      desc: "Three-layer data strategy: Yelp + Amazon backbone, AfriSenti calibration, synthetic augmentation.",
      size: "1.8 MB · PDF",
      icon: (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>),
    },
    {
      title: "Evaluation Results",
      desc: "ROUGE, BERTScore, NDCG@10, Naija Vibe Score, and human evaluation breakdown.",
      size: "1.1 MB · PDF",
      icon: (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 3v18h18"/><rect x="6" y="11" width="3" height="7"/><rect x="11" y="8" width="3" height="10"/><rect x="16" y="13" width="3" height="5"/></svg>),
    },
  ];

  return (
    <div className="page container" style={{ paddingTop: 100, paddingBottom: 80 }}>
      {readerOpen && <PaperReader onClose={() => setReaderOpen(false)} />}

      <div className="sec-head" style={{ marginBottom: 56 }}>
        <div className="eyebrow tealtxt">{t.eyebrow || 'Research & Documentation'}</div>
        <h1 style={{ fontSize: 'clamp(36px,4.6vw,56px)' }}>{t.title || 'Our paper. Our process. Our proof.'}</h1>
        <p className="lede">{t.subtitle || "The solution paper is the primary signal — it's what judges read first. Everything else here is supporting evidence."}</p>
      </div>

      <Reveal>
        <div className="paper-hero">
          <div className="paper-cover">
            <div className="cover-eyebrow">DSN × BCT · Hackathon 3.0</div>
            <h2>Naiview Intelligence: A Culturally-Aware LLM Agent System for Nigerian User Modelling and Recommendation</h2>
            <div style={{ marginTop: 24, color: 'var(--fg-mute)', fontSize: 13, lineHeight: 1.65 }}>
              Two-task LangGraph agent. 7-dimensional behavioural fingerprint. Naija Vibe Checker with regeneration loop. Hybrid retrieval and cold-start conversation. NDCG@10 +28%, Naija Vibe Score 0.81, 78% human preference.
            </div>
            <div className="cover-bottom">
              <div>TESTIMONY · AALIYAH · SHILOH</div>
              <div style={{ marginTop: 4 }}>v1.0 · MAY 2026 · 42 PP</div>
            </div>
          </div>

          <div className="col" style={{ gap: 24 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 12 }}>{t.abstractLabel || 'Abstract'}</div>
              <p style={{ fontSize: 16, lineHeight: 1.7, color: 'var(--fg-dim)', textWrap: 'pretty' }}>
                Existing review-generation and recommendation systems treat cultural context as a tag, not a feature. We argue Nigerian online behaviour — bimodal ratings, code-switching, regional dialect distributions, hedge-free emotional intensity — requires{' '}
                <span style={{ color: 'var(--fg)' }}>architecture, not decoration.</span>{' '}
                Naiview Intelligence is a LangGraph-based agent system with a 7-dimensional behavioural fingerprint, a Naija Vibe Checker, and a register-shifting Nigerian Language Module that maps standard outputs to culturally-authentic Pidgin and regional registers without breaking semantic equivalence.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button className="btn btn-primary btn-lg">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                {t.downloadBtn || 'Download Solution Paper'}
                <span className="mono" style={{ fontSize: 11, opacity: 0.7 }}>3.2 MB</span>
              </button>
              <button className="btn btn-lg" onClick={() => setReaderOpen(true)}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                {t.viewBtn || 'Read Online'}
              </button>
            </div>
            <div className="card-glass" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <div className="eyebrow">Paper Metadata</div>
                <span className="chip"><span className="chip-dot"></span>PDF</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                {[['Authors', 'Testimony, Aaliyah, Shiloh'], ['Pages', '42'], ['Date', 'May 2026'], ['Version', 'v1.0 · Final']].map(([k, v]) => (
                  <div key={k}>
                    <div className="mono dim" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.14em' }}>{k}</div>
                    <div style={{ marginTop: 4 }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Reveal>

      <Reveal>
        <div style={{ marginTop: 80 }}>
          <div className="sec-head" style={{ marginBottom: 24 }}>
            <div className="eyebrow">{t.suppLabel || 'Supplementary'}</div>
            <h2 style={{ fontSize: 'clamp(24px,2.6vw,32px)' }}>{t.suppTitle || 'Supporting documents'}</h2>
          </div>
          <div className="resource-grid">
            {supps.map(r => (
              <div key={r.title} className="resource-card">
                <div className="res-icon">{r.icon}</div>
                <h4>{r.title}</h4>
                <div className="res-desc">{r.desc}</div>
                <div className="res-meta">
                  <span className="mono dim" style={{ fontSize: 11 }}>{r.size}</span>
                  <button className="btn btn-sm"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>

      <Reveal>
        <div style={{ marginTop: 60 }}>
          <div className="eyebrow" style={{ marginBottom: 16 }}>{t.statsLabel || 'By the numbers'}</div>
          <div className="stats-bar">
            {[{ n: '16', l: 'LangChain Tools' }, { n: '12', l: 'Agent A Nodes' }, { n: '14', l: 'Agent B Nodes' }, { n: '7', l: 'Fingerprint Dims' }, { n: '6', l: 'Eval Metrics' }].map(s => (
              <div key={s.l} className="stat">
                <div className="stat-num">{s.n}</div>
                <div className="stat-label">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { PaperPage });
