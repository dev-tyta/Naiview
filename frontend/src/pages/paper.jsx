/* PAPER — Solution papers (Task A + Task B) linked from env.js */

const { useState } = React;

const ICON_DOWNLOAD = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

const ICON_EXTERNAL = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
    <polyline points="15 3 21 3 21 9"/>
    <line x1="10" y1="14" x2="21" y2="3"/>
  </svg>
);

function PaperCard({ label, title, desc, link, tag }) {
  const hasLink = link && link.trim() !== "";
  return (
    <div className="card-glass" style={{ padding: 28, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="eyebrow tealtxt" style={{ fontSize: 10 }}>{label}</div>
        <span className="chip"><span className="chip-dot"></span>{tag}</span>
      </div>
      <div>
        <h3 style={{ fontSize: 'clamp(15px,1.6vw,18px)', lineHeight: 1.35, marginBottom: 10 }}>{title}</h3>
        <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--fg-mute)' }}>{desc}</p>
      </div>
      <div style={{ marginTop: 'auto' }}>
        {hasLink ? (
          <a href={link} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-lg"
             style={{ display: 'inline-flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}>
            {ICON_DOWNLOAD}
            Open Paper
            {ICON_EXTERNAL}
          </a>
        ) : (
          <button className="btn btn-primary btn-lg" disabled style={{ opacity: 0.4, cursor: 'not-allowed' }}>
            {ICON_DOWNLOAD}
            Link not configured
          </button>
        )}
      </div>
    </div>
  );
}

function PaperPage({ navigate, vibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? 'pidgin' : 'en'] || {}).paper || {};
  const cfg = window.__NAIVIEW_CONFIG__ || {};
  const linkA = cfg.paperLinkA || "";
  const linkB = cfg.paperLinkB || "";

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
      desc: "ROUGE-L, BERTScore, Rating MAE, Naija Vibe Score, and ablation breakdown.",
      size: "1.1 MB · PDF",
      icon: (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 3v18h18"/><rect x="6" y="11" width="3" height="7"/><rect x="11" y="8" width="3" height="10"/><rect x="16" y="13" width="3" height="5"/></svg>),
    },
  ];

  return (
    <div className="page container" style={{ paddingTop: 100, paddingBottom: 80 }}>

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
              Two-task LangGraph agent. 7-dimensional behavioural fingerprint. Naija Vibe Checker with regeneration loop. Hybrid retrieval and cold-start conversation. ROUGE-L +86%, Naija Vibe Score 0.925, 100% completion rate.
            </div>
            <div className="cover-bottom">
              <div>TESTIMONY · AALIYAH · SHILOH</div>
              <div style={{ marginTop: 4 }}>v1.0 · MAY 2026</div>
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
            <div className="card-glass" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <div className="eyebrow">Paper Metadata</div>
                <span className="chip"><span className="chip-dot"></span>PDF</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                {[['Authors', 'Testimony, Aaliyah, Shiloh'], ['Tasks', 'A + B'], ['Date', 'May 2026'], ['Version', 'v1.0 · Final']].map(([k, v]) => (
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
        <div style={{ marginTop: 64 }}>
          <div className="sec-head" style={{ marginBottom: 24 }}>
            <div className="eyebrow tealtxt">{t.papersLabel || 'Solution Papers'}</div>
            <h2 style={{ fontSize: 'clamp(24px,2.6vw,32px)' }}>{t.papersTitle || 'Two tasks. Two papers.'}</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            <PaperCard
              label="Task A"
              tag="Review Generation"
              title="Culturally-Aware Nigerian Review Generation via LangGraph Agent"
              desc="7-dimensional behavioural fingerprint, persona authoring, Naija Vibe Checker with regeneration loop, NLM register shifting. ROUGE-L +86% vs baseline, Abeg Score 0.925."
              link={linkA}
            />
            <PaperCard
              label="Task B"
              tag="Recommendation"
              title="Personalised Cross-Domain Recommendation with Cold-Start Conversation"
              desc="Hybrid BM25×0.4 + Semantic×0.6 retrieval, chain-of-thought reranking, 3-turn cold-start conversation for new users. 100% completion rate, confidence 0.701."
              link={linkB}
            />
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
                  <button className="btn btn-sm">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download
                  </button>
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
