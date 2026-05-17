/* ARCHITECTURE — Animated pipeline + interactive component explorer */

const { useState, useEffect, useRef } = React;

/* ================================================================
   Node detail data — shown when a component is clicked
================================================================ */
const NODE_DETAILS = {
  client: {
    title: "React Frontend",
    color: "var(--fg-dim)", border: "var(--border)",
    rows: [
      ["Layer", "Client · Browser"],
      ["Purpose", "Demo UI. Sends REST payloads with JSON. Persists vibe mode via localStorage."],
      ["State management", "Hash routing · NaijaVibeMode (localStorage) · Cold-start session (sessionStorage)"],
    ],
  },
  fastapi: {
    title: "FastAPI Layer",
    color: "var(--lavender)", border: "rgba(139,126,200,0.45)",
    rows: [
      ["Endpoints", "POST /task-a/generate · POST /task-b/recommend · GET /healthz"],
      ["Middleware", "Request IDs, structured JSON logging, CORS open to frontend origin"],
      ["Auth", "JWT (HS256), 24 h expiry, signed with JWT_SECRET_KEY. Sessions table tracks revoked tokens."],
      ["Flow", "Validate payload (Pydantic) → initialise TaskAState/TaskBState → invoke LangGraph → return typed JSON"],
    ],
  },
  agentA: {
    title: "Agent A — Review Generation",
    color: "var(--teal)", border: "rgba(0,212,170,0.45)",
    rows: [
      ["Type", "LangGraph StateGraph · 12 typed nodes"],
      ["State", "TaskAState (TypedDict) — immutable across nodes; each node returns {**state, field: value}"],
      ["LLM calls", "generate_draft → Gemini 2.5 Pro · analyse_item + vibe_check → Gemini 2.0 Flash"],
      ["Regen loop", "vibe_check → plan_regen → author_persona (loop, max 2 retries, only in active mode)"],
      ["Output", "final_review, final_rating, confidence, vibe_score, fingerprint_match, reasoning_trace"],
    ],
  },
  agentB: {
    title: "Agent B — Recommendation Engine",
    color: "var(--amber)", border: "rgba(232,168,56,0.45)",
    rows: [
      ["Type", "LangGraph StateGraph · 14 typed nodes"],
      ["Two paths", "Existing user: load_history → fingerprint → region. Cold-start: 3-turn chat → bootstrap_fingerprint"],
      ["Merge point", "Both paths converge at retrieve_candidates (hybrid BM25×0.4 + Semantic×0.6)"],
      ["LLM calls", "rerank → Gemini 2.5 Pro · cold_start_interview + generate_explanations → Gemini 2.0 Flash"],
      ["Confidence gate", "compute_confidence → if conf < 0.75 → gen_clarifying_question · else → finalise"],
    ],
  },
  tools: {
    title: "Shared Tool Registry",
    color: "var(--fg)", border: "var(--border-strong)",
    rows: [
      ["Count", "16 LangChain @tool-decorated functions with Pydantic I/O schemas"],
      ["Agent A only", "analyse_item_for_user, fetch_few_shot_examples, run_naija_vibe_check, save_review"],
      ["Agent B only", "retrieve_candidates_hybrid, rerank_candidates, cold_start_interview, diversity_check"],
      ["Shared", "load_user_history, build_behavioural_fingerprint, detect_nigerian_region, apply_nigerian_taxonomy"],
      ["Contract", "Every tool declares input schema, output schema, and failure mode. No inline agent calls."],
    ],
  },
  chroma: {
    title: "ChromaDB — Episodic Memory",
    color: "var(--teal)", border: "rgba(0,212,170,0.35)",
    rows: [
      ["Holds", "All past reviews per user, embedded + metadata. Append-only."],
      ["Layout", "One collection per user (or single collection partitioned by user_id — TBD by perf testing)"],
      ["Query budget", "< 50 ms for users with ≤ 500 reviews"],
      ["Persist path", "./data/chroma (configurable via CHROMA_PERSIST_DIR)"],
    ],
  },
  faiss: {
    title: "FAISS — Item Index",
    color: "var(--teal)", border: "rgba(0,212,170,0.35)",
    rows: [
      ["Holds", "All items (Yelp + Amazon dataset), embedded globally"],
      ["Index type", "Flat IP (inner product) index — exact search, no approximation"],
      ["Embedding model", "BAAI/bge-m3 via sentence-transformers"],
      ["Lifecycle", "Built once at data-prep time. Rebuilt on dataset refresh."],
      ["Used by", "retrieve_similar_items (Task A), retrieve_candidates_hybrid (Task B)"],
    ],
  },
  redis: {
    title: "Redis — Fingerprint Cache",
    color: "var(--amber)", border: "rgba(232,168,56,0.35)",
    rows: [
      ["Holds", "Computed Fingerprint objects, keyed by (user_id, last_review_timestamp)"],
      ["TTL", "24 hours. Invalidated immediately when a new review is saved."],
      ["Dev fallback", "Python dict (cache_backend = 'memory') — no Redis needed locally"],
      ["Config", "REDIS_URL env var · FINGERPRINT_CACHE_TTL_HOURS env var"],
    ],
  },
  llm: {
    title: "LLM Router — Gemini",
    color: "var(--lavender)", border: "rgba(139,126,200,0.35)",
    rows: [
      ["Generation tier", "Gemini 2.5 Pro — review drafts, chain-of-thought reranking, explanation generation"],
      ["Utility tier", "Gemini 2.0 Flash — item analysis, vibe scoring, cold-start parsing, clarifying questions"],
      ["Interface", "router.call_with_retry(tier, prompt, max_tokens) — single call point for both tiers"],
      ["Retry policy", "ResourceExhausted → exponential backoff · GoogleAPIError → retry once"],
      ["Config", "GEMINI_API_KEY · GEMINI_GENERATION_MODEL · GEMINI_UTILITY_MODEL env vars"],
    ],
  },
  nlm: {
    title: "Nigerian Language Module",
    color: "var(--amber)", border: "rgba(232,168,56,0.35)",
    rows: [
      ["What it is", "NOT a translator. A register-shifter — maps standard output to culturally-authentic Nigerian voice."],
      ["Components", "PhraseLibrary (AfriSenti + NaijaSenti phrases by region×sentiment), PidginMapper, RegionSignals, CodeSwitcher"],
      ["Activation", "Applied only in active Naija Vibe Mode. In passive mode, the Vibe Checker runs but NLM is skipped."],
      ["Code-switch", "Yoruba (Lagos), Igbo (Enugu/Anambra), Hausa (Kano) loanword injection by detected region"],
      ["Data source", "Curated phrase library in data/phrase_library/ · versioned in git"],
    ],
  },
};

/* ================================================================
   Animated SVG Flow Diagram
================================================================ */
function FlowDiagram({ selectedNode, onNodeClick }) {
  const [vis, setVis] = useState({});
  const svgRef = useRef(null);

  const SEQUENCE = [
    ['client',  0],
    ['l1',      280],
    ['fastapi', 520],
    ['l2',      800],
    ['agentA',  1040],
    ['agentB',  1040],
    ['l4',      1300],
    ['l5',      1300],
    ['tools',   1520],
    ['l6',      1760],
    ['infra',   2000],
    ['l7',      2260],
    ['nlm',     2500],
  ];

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const all = {};
      SEQUENCE.forEach(([k]) => { all[k] = true; });
      setVis(all);
      return;
    }
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        SEQUENCE.forEach(([key, delay]) => {
          setTimeout(() => setVis(v => ({ ...v, [key]: true })), delay);
        });
        io.disconnect();
      }
    }, { threshold: 0.08 });
    if (svgRef.current) io.observe(svgRef.current);
    return () => io.disconnect();
  }, []);

  const nStyle = (key, accent) => ({
    opacity: vis[key] ? 1 : 0,
    transition: 'opacity 0.45s ease, filter 0.2s ease',
    cursor: 'pointer',
    filter: selectedNode === key
      ? `drop-shadow(0 0 10px ${accent})`
      : 'none',
  });

  const lStyle = (key) => ({
    strokeDashoffset: vis[key] ? 0 : 1,
    transition: 'stroke-dashoffset 0.65s cubic-bezier(0.4,0,0.2,1)',
  });

  const sel = selectedNode;
  const TB = 'var(--teal)'; const AB = 'var(--amber)'; const LV = 'var(--lavender)';
  const TSOFT = 'rgba(0,212,170,0.08)'; const ASOFT = 'rgba(232,168,56,0.08)'; const LSOFT = 'rgba(139,126,200,0.08)';
  const TBORDER = (k) => sel === k ? TB : 'rgba(0,212,170,0.4)';
  const ABORDER = (k) => sel === k ? AB : 'rgba(232,168,56,0.4)';
  const LBORDER = (k) => sel === k ? LV : 'rgba(139,126,200,0.35)';
  const GBORDER = (k) => sel === k ? 'var(--border-strong)' : 'var(--border)';
  const SW = (k) => sel === k ? 2.5 : 1.5;

  return (
    <div ref={svgRef} style={{ width: '100%', overflowX: 'auto' }}>
      <svg viewBox="0 0 960 615" width="100%" style={{ minWidth: 480, display: 'block' }}
           aria-label="System architecture flow diagram" role="img">
        <defs>
          {[['teal', TB], ['amber', AB], ['lav', LV], ['mute', 'var(--border-strong)']].map(([id, col]) => (
            <marker key={id} id={`arr-${id}`} markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
              <path d="M 0 0 L 7 3.5 L 0 7 z" fill={col} opacity="0.8"/>
            </marker>
          ))}
        </defs>

        {/* ── Lines ── */}
        {/* Client → FastAPI */}
        <path d="M 480 64 L 480 105" fill="none" stroke="var(--border-strong)"
              strokeWidth="1.5" pathLength="1" strokeDasharray="1"
              markerEnd="url(#arr-mute)" style={lStyle('l1')}/>

        {/* FastAPI → AgentA */}
        <path d="M 330 167 Q 190 195 190 215" fill="none" stroke={TB}
              strokeWidth="1.5" opacity="0.7" pathLength="1" strokeDasharray="1"
              markerEnd="url(#arr-teal)" style={lStyle('l2')}/>

        {/* FastAPI → AgentB */}
        <path d="M 630 167 Q 770 195 770 215" fill="none" stroke={AB}
              strokeWidth="1.5" opacity="0.7" pathLength="1" strokeDasharray="1"
              markerEnd="url(#arr-amber)" style={lStyle('l2')}/>

        {/* AgentA → Tools */}
        <path d="M 190 285 Q 190 318 350 333" fill="none" stroke={TB}
              strokeWidth="1.5" opacity="0.5" pathLength="1" strokeDasharray="1"
              markerEnd="url(#arr-teal)" style={lStyle('l4')}/>

        {/* AgentB → Tools */}
        <path d="M 770 285 Q 770 318 610 333" fill="none" stroke={AB}
              strokeWidth="1.5" opacity="0.5" pathLength="1" strokeDasharray="1"
              markerEnd="url(#arr-amber)" style={lStyle('l5')}/>

        {/* Tools → infra distribution */}
        <path d="M 480 391 L 480 438" fill="none" stroke="var(--border-strong)"
              strokeWidth="1.5" pathLength="1" strokeDasharray="1" style={lStyle('l6')}/>
        <path d="M 134 438 L 826 438" fill="none" stroke="var(--border-strong)"
              strokeWidth="1.5" pathLength="1" strokeDasharray="1" style={lStyle('l6')}/>
        {[134, 330, 524, 720].map(x => (
          <path key={x} d={`M ${x} 438 L ${x} 443`} fill="none" stroke="var(--border-strong)"
                strokeWidth="1.5" pathLength="1" strokeDasharray="1"
                markerEnd="url(#arr-mute)" style={lStyle('l6')}/>
        ))}

        {/* Infra → NLM */}
        {[134, 330, 524, 720].map(x => (
          <path key={x} d={`M ${x} 503 L ${x} 510`} fill="none" stroke="var(--border-strong)"
                strokeWidth="1" pathLength="1" strokeDasharray="1" style={lStyle('l7')}/>
        ))}
        <path d="M 134 510 L 826 510" fill="none" stroke="var(--border-strong)"
              strokeWidth="1.5" pathLength="1" strokeDasharray="1" style={lStyle('l7')}/>
        <path d="M 480 510 L 480 555" fill="none" stroke={AB}
              strokeWidth="1.5" opacity="0.7" pathLength="1" strokeDasharray="1"
              markerEnd="url(#arr-amber)" style={lStyle('l7')}/>

        {/* ── Nodes ── */}

        {/* CLIENT */}
        <g onClick={() => onNodeClick(sel === 'client' ? null : 'client')} style={nStyle('client', 'var(--fg-dim)')}>
          <rect x="380" y="12" width="200" height="52" rx="8"
                fill="var(--surface)" stroke={GBORDER('client')} strokeWidth={SW('client')}/>
          <text x="480" y="34" textAnchor="middle" fontFamily="var(--f-display)" fontSize="14" fill="var(--fg)" fontWeight="500">React Frontend</text>
          <text x="480" y="52" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9.5" fill="var(--fg-mute)" letterSpacing="0.1em">CLIENT LAYER</text>
        </g>

        {/* FASTAPI */}
        <g onClick={() => onNodeClick(sel === 'fastapi' ? null : 'fastapi')} style={nStyle('fastapi', LV)}>
          <rect x="100" y="105" width="760" height="62" rx="8"
                fill={LSOFT} stroke={LBORDER('fastapi')} strokeWidth={SW('fastapi')}/>
          <text x="480" y="128" textAnchor="middle" fontFamily="var(--f-display)" fontSize="14" fill={LV} fontWeight="500">FastAPI Layer</text>
          <text x="305" y="153" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="10" fill="var(--fg-mute)">POST /task-a/generate</text>
          <line x1="480" y1="113" x2="480" y2="163" stroke="rgba(139,126,200,0.2)" strokeWidth="1" strokeDasharray="3,3"/>
          <text x="655" y="153" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="10" fill="var(--fg-mute)">POST /task-b/recommend</text>
        </g>

        {/* AGENT A */}
        <g onClick={() => onNodeClick(sel === 'agentA' ? null : 'agentA')} style={nStyle('agentA', TB)}>
          <rect x="60" y="215" width="260" height="70" rx="8"
                fill={TSOFT} stroke={TBORDER('agentA')} strokeWidth={SW('agentA')}/>
          <text x="190" y="239" textAnchor="middle" fontFamily="var(--f-display)" fontSize="14" fill={TB} fontWeight="500">Agent A</text>
          <text x="190" y="257" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="10" fill="var(--fg-dim)">Review Generation</text>
          <text x="190" y="274" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill={TB} letterSpacing="0.07em">LangGraph · 12 nodes</text>
        </g>

        {/* AGENT B */}
        <g onClick={() => onNodeClick(sel === 'agentB' ? null : 'agentB')} style={nStyle('agentB', AB)}>
          <rect x="640" y="215" width="260" height="70" rx="8"
                fill={ASOFT} stroke={ABORDER('agentB')} strokeWidth={SW('agentB')}/>
          <text x="770" y="239" textAnchor="middle" fontFamily="var(--f-display)" fontSize="14" fill={AB} fontWeight="500">Agent B</text>
          <text x="770" y="257" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="10" fill="var(--fg-dim)">Recommendations</text>
          <text x="770" y="274" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill={AB} letterSpacing="0.07em">LangGraph · 14 nodes</text>
        </g>

        {/* TOOLS */}
        <g onClick={() => onNodeClick(sel === 'tools' ? null : 'tools')} style={nStyle('tools', 'var(--fg)')}>
          <rect x="220" y="333" width="520" height="58" rx="8"
                fill="var(--surface)" stroke={GBORDER('tools')} strokeWidth={SW('tools')}/>
          <text x="480" y="357" textAnchor="middle" fontFamily="var(--f-display)" fontSize="14" fill="var(--fg)" fontWeight="500">Shared Tool Registry</text>
          <text x="480" y="375" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9.5" fill="var(--fg-mute)" letterSpacing="0.06em">16 LangChain tools · Pydantic I/O contracts · explicit failure modes</text>
        </g>

        {/* INFRA — 4 boxes */}
        {/* ChromaDB */}
        <g onClick={() => onNodeClick(sel === 'chroma' ? null : 'chroma')} style={nStyle('infra', TB)}>
          <rect x="46" y="443" width="176" height="60" rx="7"
                fill="var(--surface)" stroke={TBORDER('chroma')} strokeWidth={sel === 'chroma' ? 2 : 1}/>
          <text x="134" y="467" textAnchor="middle" fontFamily="var(--f-display)" fontSize="12.5" fill={TB} fontWeight="500">ChromaDB</text>
          <text x="134" y="484" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-mute)">Episodic Memory</text>
          <text x="134" y="496" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="8" fill="var(--fg-faint)">per-user vectors</text>
        </g>
        {/* FAISS */}
        <g onClick={() => onNodeClick(sel === 'faiss' ? null : 'faiss')} style={nStyle('infra', TB)}>
          <rect x="242" y="443" width="176" height="60" rx="7"
                fill="var(--surface)" stroke={TBORDER('faiss')} strokeWidth={sel === 'faiss' ? 2 : 1}/>
          <text x="330" y="467" textAnchor="middle" fontFamily="var(--f-display)" fontSize="12.5" fill={TB} fontWeight="500">FAISS</text>
          <text x="330" y="484" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-mute)">Item Index</text>
          <text x="330" y="496" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="8" fill="var(--fg-faint)">BAAI/bge-m3</text>
        </g>
        {/* Redis */}
        <g onClick={() => onNodeClick(sel === 'redis' ? null : 'redis')} style={nStyle('infra', AB)}>
          <rect x="438" y="443" width="172" height="60" rx="7"
                fill="var(--surface)" stroke={ABORDER('redis')} strokeWidth={sel === 'redis' ? 2 : 1}/>
          <text x="524" y="467" textAnchor="middle" fontFamily="var(--f-display)" fontSize="12.5" fill={AB} fontWeight="500">Redis</text>
          <text x="524" y="484" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-mute)">Fingerprint Cache</text>
          <text x="524" y="496" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="8" fill="var(--fg-faint)">24 h TTL</text>
        </g>
        {/* LLM Router */}
        <g onClick={() => onNodeClick(sel === 'llm' ? null : 'llm')} style={nStyle('infra', LV)}>
          <rect x="630" y="443" width="284" height="60" rx="7"
                fill={LSOFT} stroke={LBORDER('llm')} strokeWidth={sel === 'llm' ? 2 : 1}/>
          <text x="772" y="467" textAnchor="middle" fontFamily="var(--f-display)" fontSize="12.5" fill={LV} fontWeight="500">LLM Router</text>
          <text x="772" y="484" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-mute)">Gemini 2.5 Pro · 2.0 Flash</text>
          <text x="772" y="496" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="8" fill="var(--fg-faint)">generation + utility tiers</text>
        </g>

        {/* NLM */}
        <g onClick={() => onNodeClick(sel === 'nlm' ? null : 'nlm')} style={nStyle('nlm', AB)}>
          <rect x="215" y="555" width="530" height="55" rx="8"
                fill={ASOFT} stroke={ABORDER('nlm')} strokeWidth={SW('nlm')}/>
          <text x="480" y="578" textAnchor="middle" fontFamily="var(--f-display)" fontSize="13.5" fill={AB} fontWeight="500">Nigerian Language Module</text>
          <text x="480" y="597" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-mute)" letterSpacing="0.06em">Pidgin Mapper · Region Signals · Code-Switch · AfriSenti Phrases</text>
        </g>

        {/* Output label below NLM */}
        <text x="480" y="625" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-faint)" letterSpacing="0.14em">→ ReviewOutput / RecommendationOutput</text>

        {/* "click node" hint */}
        <text x="480" y="8" textAnchor="middle" fontFamily="var(--f-mono)" fontSize="9" fill="var(--fg-faint)" letterSpacing="0.12em">CLICK ANY NODE FOR DETAILS</text>
      </svg>
    </div>
  );
}

/* ================================================================
   Node detail panel — shown below the diagram when a node is clicked
================================================================ */
function NodeDetailPanel({ nodeId, onClose }) {
  const d = NODE_DETAILS[nodeId];
  if (!d) return null;

  return (
    <div className="node-detail-panel" style={{
      marginTop: 16,
      padding: 24,
      background: 'var(--surface)',
      border: `1px solid ${d.border}`,
      borderRadius: 'var(--r-lg)',
      animation: 'float-in 0.3s ease',
      position: 'relative',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
        <div>
          <div style={{ fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: d.color, marginBottom: 4 }}>COMPONENT</div>
          <h3 style={{ fontSize: 20, color: d.color, margin: 0 }}>{d.title}</h3>
        </div>
        <button onClick={onClose} style={{
          background: 'transparent', border: '1px solid var(--border)', color: 'var(--fg-mute)',
          borderRadius: 'var(--r-sm)', padding: '4px 10px', cursor: 'pointer', fontSize: 12,
          fontFamily: 'var(--f-mono)', letterSpacing: '0.08em',
        }}>✕ CLOSE</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
        {d.rows.map(([k, v]) => (
          <div key={k} style={{
            padding: '12px 14px', background: 'var(--bg-elev)',
            border: '1px solid var(--border)', borderRadius: 'var(--r)',
          }}>
            <div style={{ fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: d.color, marginBottom: 6 }}>{k}</div>
            <div style={{ fontSize: 13, color: 'var(--fg-dim)', lineHeight: 1.55 }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ================================================================
   Deep-dive: fingerprint table, vibe check, agent flows
================================================================ */
function FingerprintTable() {
  const dims = [
    { n: '01', name: 'Generosity',         color: 'teal',  how: 'mean(user_stars − platform_avg), normalised [0,1]',    what: 'Generous praiser or harsh critic?' },
    { n: '02', name: 'Verbosity',           color: 'teal',  how: 'quantile rank of mean word count across all users',    what: 'Brief or detailed writer?' },
    { n: '03', name: 'Emotional Intensity', color: 'amber', how: 'intensifier words + exclamations per 100 tokens',      what: 'How emotionally expressive?' },
    { n: '04', name: 'Topic Focus',         color: 'amber', how: 'top-3 noun phrases (spaCy), frequency > 30%',          what: 'What do they always mention?' },
    { n: '05', name: 'Consistency',         color: 'lav',   how: 'Pearson corr(VADER sentiment, star rating) → [0,1]',   what: 'Do their words match their stars?' },
    { n: '06', name: 'Recency Weight',      color: 'lav',   how: 'exponential decay coefficient on review timestamps',   what: 'How much do recent reviews dominate?' },
    { n: '07', name: 'Naija Slang Index',   color: 'rose',  how: 'fraction of tokens matching Nigerian phrase library',  what: 'How Naija does this person write?' },
  ];
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, minWidth: 580 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {['#', 'Dimension', 'How it is computed', 'What it captures'].map(h => (
              <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.12em', color: 'var(--fg-mute)', fontWeight: 400 }}>{h.toUpperCase()}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dims.map(d => (
            <tr key={d.n} style={{ borderBottom: '1px solid var(--border)' }}>
              <td style={{ padding: '10px 12px', fontFamily: 'var(--f-mono)', fontSize: 11, color: 'var(--fg-faint)' }}>{d.n}</td>
              <td style={{ padding: '10px 12px' }}>
                <span style={{ fontWeight: 600, fontSize: 13, color: d.color === 'teal' ? 'var(--teal)' : d.color === 'amber' ? 'var(--amber)' : d.color === 'lav' ? 'var(--lavender)' : 'var(--rose)' }}>{d.name}</span>
              </td>
              <td style={{ padding: '10px 12px', fontFamily: 'var(--f-mono)', fontSize: 11, color: 'var(--fg-mute)', maxWidth: 260 }}>{d.how}</td>
              <td style={{ padding: '10px 12px', fontSize: 13, color: 'var(--fg-dim)', maxWidth: 200 }}>{d.what}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 14 }}>
        {[
          { label: 'Redis cache · (user_id, last_review_ts) · TTL 24 h', color: 'var(--amber)' },
          { label: 'Cold-start: bootstrapped with wide confidence intervals', color: 'var(--teal)' },
          { label: 'Min 3 reviews for reliable computation', color: 'var(--fg-mute)' },
        ].map(chip => (
          <span key={chip.label} className="chip" style={{ fontSize: 11, color: chip.color, borderColor: chip.color === 'var(--fg-mute)' ? 'var(--border)' : chip.color }}>
            <span className="chip-dot" style={{ background: chip.color }}></span>{chip.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function VibeCheckViz() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <div style={{ padding: '20px 24px', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--r)', gridColumn: '1 / -1' }}>
        <div className="mono dim" style={{ fontSize: 10, letterSpacing: '0.14em', marginBottom: 14 }}>ABEG SCORE FORMULA</div>
        <div style={{ fontFamily: 'var(--f-mono)', fontSize: 15, lineHeight: 2.4, color: 'var(--fg)' }}>
          <span className="lavtxt">abeg_score</span><span style={{ color: 'var(--fg-mute)' }}> = </span>
          <span className="tealtxt">0.40</span><span style={{ color: 'var(--fg-mute)' }}> × cultural_authenticity</span>
          <br/>
          <span style={{ paddingLeft: 120 }}>
            <span className="tealtxt">+ 0.35</span><span style={{ color: 'var(--fg-mute)' }}> × cultural_accuracy</span>
          </span>
          <br/>
          <span style={{ paddingLeft: 120 }}>
            <span className="tealtxt">+ 0.25</span><span style={{ color: 'var(--fg-mute)' }}> × persona_consistency</span>
          </span>
        </div>
      </div>
      <div style={{ padding: '16px', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)' }}>
        <div className="mono dim" style={{ fontSize: 10, letterSpacing: '0.14em', marginBottom: 8 }}>PASSIVE MODE</div>
        <div style={{ fontSize: 13, color: 'var(--fg-dim)', lineHeight: 1.55 }}>Always runs — even when Naija Vibe is off. Score is attached to output silently. No regeneration triggered.</div>
      </div>
      <div style={{ padding: '16px', background: 'rgba(232,168,56,0.05)', border: '1px solid rgba(232,168,56,0.3)', borderRadius: 'var(--r-sm)' }}>
        <div className="mono ambertxt" style={{ fontSize: 10, letterSpacing: '0.14em', marginBottom: 8 }}>ACTIVE MODE · Naija Vibe ON</div>
        <div style={{ fontSize: 13, color: 'var(--fg-dim)', lineHeight: 1.55 }}>
          abeg &lt; 0.70 → <span className="mono" style={{ color: 'var(--rose)' }}>plan_regen</span> → <span className="mono ambertxt">author_persona</span> loop. Max 2 retries before finalise.
        </div>
      </div>
      <div style={{ padding: '14px 16px', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)', gridColumn: '1 / -1' }}>
        <div className="mono dim" style={{ fontSize: 10, letterSpacing: '0.14em', marginBottom: 10 }}>BEFORE (abeg 0.58 · regen triggered) → AFTER (abeg 0.84 · pass)</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 12, alignItems: 'center' }}>
          <div style={{ padding: '10px 14px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', fontSize: 13, color: 'var(--fg-mute)' }}>
            "The food was very good and I enjoyed my experience at this establishment."
          </div>
          <div className="mono" style={{ fontSize: 11, color: 'var(--amber)', letterSpacing: '0.08em', textAlign: 'center' }}>PLAN<br/>REGEN<br/>→</div>
          <div style={{ padding: '10px 14px', background: 'rgba(232,168,56,0.06)', border: '1px solid rgba(232,168,56,0.35)', borderRadius: 'var(--r)', fontSize: 13, color: 'var(--fg)' }}>
            "This food sweet die, I no go lie. Waiter dem sabi their work, no cap."
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentBViz() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <div style={{ padding: '16px 20px', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--r)' }}>
        <div className="mono dim" style={{ fontSize: 10, letterSpacing: '0.14em', marginBottom: 10 }}>HYBRID RETRIEVAL SCORE</div>
        <div style={{ fontFamily: 'var(--f-mono)', fontSize: 14, color: 'var(--fg)' }}>
          <span className="lavtxt">score</span> = <span className="tealtxt">0.4</span> × BM25 + <span className="tealtxt">0.6</span> × Semantic
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: 'var(--fg-mute)' }}>FAISS flat IP · <span className="mono tealtxt">BAAI/bge-m3</span> · top-20 per source, deduplicated</div>
      </div>
      <div style={{ padding: '16px 20px', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--r)' }}>
        <div className="mono dim" style={{ fontSize: 10, letterSpacing: '0.14em', marginBottom: 10 }}>DIVERSITY CHECK</div>
        <div style={{ fontFamily: 'var(--f-mono)', fontSize: 14, color: 'var(--fg)' }}>
          <span className="lavtxt">diversity</span> = 1 − <span className="tealtxt">(max_cat / total)</span>
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: 'var(--fg-mute)' }}>Swap lowest-ranked dominant item if diversity &lt; 0.60</div>
      </div>
      {[
        { num: '01', title: 'check_user_history', desc: 'Existing user? → load_history path. New? → cold_start_turn path.', color: 'teal' },
        { num: '02', title: 'Hybrid retrieval', desc: 'BM25 × 0.4 + Semantic × 0.6 over FAISS. Top-20 candidates.', color: 'teal' },
        { num: '03', title: 'rerank', desc: 'Gemini 2.5 Pro chain-of-thought reranker against fingerprint.', color: 'amber' },
        { num: '04', title: 'diversity_check + taxonomy', desc: 'Ensure category spread ≥ 0.60. Apply Nigerian taxonomy overlay.', color: 'lav' },
        { num: '05', title: 'generate_explanations', desc: 'Gemini 2.0 Flash — Pidgin or English depending on naija_vibe_mode.', color: 'amber' },
        { num: '06', title: 'confidence_gate', desc: 'conf ≥ 0.75 → finalise. conf < 0.75 → gen_clarifying_question.', color: 'rose' },
      ].map(s => (
        <div key={s.num} style={{ padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <span className="mono" style={{ fontSize: 11, color: s.color === 'teal' ? 'var(--teal)' : s.color === 'amber' ? 'var(--amber)' : s.color === 'lav' ? 'var(--lavender)' : 'var(--rose)', flexShrink: 0 }}>{s.num}</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>{s.title}</div>
            <div style={{ fontSize: 12, color: 'var(--fg-mute)', fontFamily: 'var(--f-mono)' }}>{s.desc}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ================================================================
   Main page
================================================================ */
function ArchitecturePage({ vibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? 'pidgin' : 'en'] || {}).arch || {};
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeTab, setActiveTab] = useState('fingerprint');

  const TABS = [
    { id: 'fingerprint', label: '7-Dim Fingerprint' },
    { id: 'vibe', label: 'Naija Vibe Check' },
    { id: 'agentb', label: 'Agent B Pipeline' },
  ];

  return (
    <div className="page container" style={{ paddingTop: 100, paddingBottom: 80 }}>
      {/* Header */}
      <div className="sec-head" style={{ marginBottom: 0, maxWidth: 800 }}>
        <div className="eyebrow tealtxt">{t.eyebrow || 'How It Works'}</div>
        <h1 style={{ fontSize: 'clamp(36px,4.6vw,56px)' }}>{t.title || 'The agent, walked through.'}</h1>
        <p className="lede">{t.subtitle || 'Full system flow — from HTTP request to culturally-grounded output. Click any component to see what it actually does.'}</p>
      </div>

      {/* Animated Pipeline */}
      <Reveal>
        <div style={{ marginTop: 48 }}>
          <FlowDiagram selectedNode={selectedNode} onNodeClick={setSelectedNode} />
          {selectedNode && (
            <NodeDetailPanel nodeId={selectedNode} onClose={() => setSelectedNode(null)} />
          )}
        </div>
      </Reveal>

      {/* Deep-dive tabs */}
      <Reveal>
        <div style={{ marginTop: 72 }}>
          <div className="eyebrow" style={{ marginBottom: 20 }}>Technical Deep Dive</div>
          {/* Tab bar */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 28 }}>
            {TABS.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className="btn btn-sm"
                style={{
                  background: activeTab === tab.id ? 'var(--teal-soft)' : 'var(--surface)',
                  color: activeTab === tab.id ? 'var(--teal)' : 'var(--fg-mute)',
                  borderColor: activeTab === tab.id ? 'var(--teal)' : 'var(--border)',
                }}>
                {tab.label}
              </button>
            ))}
          </div>

          <div className="card" style={{ padding: 28 }}>
            {activeTab === 'fingerprint' && (
              <>
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ fontSize: 20, marginBottom: 6 }}>{t.scene03title || 'The 7-dimensional fingerprint.'}</h3>
                  <p style={{ fontSize: 15, color: 'var(--fg-mute)' }}>{t.scene03desc || 'Every user has a behavioural fingerprint across 7 dimensions. Cached in Redis with a 24-hour TTL. Cold-start users get a bootstrapped fingerprint — never breaks.'}</p>
                </div>
                <FingerprintTable />
              </>
            )}
            {activeTab === 'vibe' && (
              <>
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ fontSize: 20, marginBottom: 6 }}>{t.scene04title || 'Naija Vibe Check — always on.'}</h3>
                  <p style={{ fontSize: 15, color: 'var(--fg-mute)' }}>{t.scene04desc || 'Every generated review passes through the Vibe Checker. Passive mode scores silently. Active mode regenerates up to 2 times if Abeg Score is below 0.70.'}</p>
                </div>
                <VibeCheckViz />
              </>
            )}
            {activeTab === 'agentb' && (
              <>
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ fontSize: 20, marginBottom: 6 }}>{t.scene05title || 'Agent B: Retrieve, rerank, diversify.'}</h3>
                  <p style={{ fontSize: 15, color: 'var(--fg-mute)' }}>{t.scene05desc || 'Task B opens with hybrid BM25 + semantic retrieval over FAISS. Top-20 candidates are reranked by Gemini 2.5 Pro. Diversity is enforced before explanations are generated.'}</p>
                </div>
                <AgentBViz />
              </>
            )}
          </div>
        </div>
      </Reveal>

      {/* Tech stack */}
      <Reveal>
        <div className="eyebrow" style={{ marginTop: 60, marginBottom: 14 }}>{t.stackLabel || 'The real stack'}</div>
        <div className="tech-bar">
          {['LangGraph', 'LangChain', 'FastAPI', 'Gemini 2.5 Pro', 'Gemini 2.0 Flash', 'ChromaDB', 'FAISS', 'Redis', 'spaCy', 'BAAI/bge-m3', 'sentence-transformers', 'Docker', 'React'].map(l => (
            <div key={l} className="tech-pill"><span className="dot"></span>{l}</div>
          ))}
        </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { ArchitecturePage });
