/* LANDING PAGE — Storytelling Hero Experience */

const { useState, useEffect } = React;

function HeroBackground() {
  return (
    <svg className="hero-bg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <radialGradient id="rg1" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#00D4AA" stopOpacity="0.4"/>
          <stop offset="100%" stopColor="#00D4AA" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="rg2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#E8A838" stopOpacity="0.3"/>
          <stop offset="100%" stopColor="#E8A838" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="rg3" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#8B7EC8" stopOpacity="0.3"/>
          <stop offset="100%" stopColor="#8B7EC8" stopOpacity="0"/>
        </radialGradient>
      </defs>
      <circle cx="200" cy="200" r="280" fill="url(#rg1)">
        <animate attributeName="cx" values="200;240;200" dur="14s" repeatCount="indefinite"/>
      </circle>
      <circle cx="950" cy="300" r="240" fill="url(#rg3)">
        <animate attributeName="cy" values="300;340;300" dur="16s" repeatCount="indefinite"/>
      </circle>
      <circle cx="700" cy="650" r="280" fill="url(#rg2)">
        <animate attributeName="cx" values="700;680;700" dur="18s" repeatCount="indefinite"/>
      </circle>
      {Array.from({ length: 40 }).map((_, i) => {
        const x = (i % 8) * 150 + 75 + (Math.sin(i) * 30);
        const y = Math.floor(i / 8) * 160 + 80 + (Math.cos(i) * 20);
        const r = 1 + (i % 3) * 0.5;
        return (
          <circle key={i} cx={x} cy={y} r={r} fill="#3A3A42" opacity={0.7}>
            <animate attributeName="opacity" values="0.3;0.8;0.3" dur={`${4 + (i % 5)}s`} repeatCount="indefinite" begin={`${i * 0.1}s`}/>
          </circle>
        );
      })}
      {Array.from({ length: 18 }).map((_, i) => {
        const x1 = (i * 78) % 1200;
        const y1 = (i * 53) % 800;
        const x2 = ((i + 3) * 78) % 1200;
        const y2 = ((i + 3) * 53) % 800;
        return (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#2A2A2E" strokeWidth="0.6" opacity="0.4"/>
        );
      })}
    </svg>
  );
}

const FP_DIMS = [
  { label: "Generosity" },
  { label: "Verbosity" },
  { label: "Emotional Intensity" },
  { label: "Topic Focus" },
  { label: "Consistency" },
  { label: "Recency Weight" },
  { label: "Naija Slang Index" },
];

function Landing({ navigate, vibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).landing || {};
  const tTaskA = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).taskA || {};
  const tTaskB = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).taskB || {};

  return (
    <div className="page landing">
      {/* ===== HERO ===== */}
      {/* Full-viewport hero — background must be outside .container */}
      <section className="hero" aria-label="Hero">
        <HeroBackground />
        <div className="container hero-inner">
          <div className="hero-content">
            <div className="hero-eyebrow fade-in">
              <span className="pulse" aria-hidden="true"></span>
              DSN × BCT · LLM Agent Challenge 3.0 · May 2026
            </div>
            <h1 className="fade-in-d1">
              Naiview <span className="accent">Intelligence</span>
            </h1>
            <p className="hero-sub fade-in-d2">
              Nigerian AI that understands <em>suya reviewers, VI foodies, and Kano buyers</em> — not just "African users."
            </p>
            <div className="hero-cta fade-in-d3">
              <button className="btn btn-primary btn-lg" onClick={() => navigate("/task-a")}>
                {tTaskA.generateBtn || "Generate a Review"}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </button>
              <button className="btn btn-lg" onClick={() => navigate("/task-b")}>
                {tTaskB.getRecsBtn || "Get Recommendations"}
              </button>
              <button className="btn btn-ghost btn-lg" onClick={() => navigate("/paper")}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                {vibe ? "Read Paper" : "Read Our Paper"}
              </button>
            </div>
          </div>
        </div>
        <div className="scroll-indicator" aria-hidden="true">
          <span>{t.scrollHint || "Scroll to see why this matters"}</span>
          <div className="arrow"></div>
        </div>
      </section>

      {/* ===== PROOF SECTION ===== */}
      <section className="proof-section" aria-label="Evaluation results">
        <div className="container">
          <div className="proof-eyebrow-row fade-in">
            <span className="eyebrow">Evaluation Results</span>
            <span className="mono dim" style={{ fontSize: 11 }}>vs direct-LLM baseline · n=30 held-out · seed 42 · 2026-05-24</span>
          </div>
          <div className="proof-grid fade-in-d1">
            {[
              { num: "+86%",  color: "var(--teal)",     label: "ROUGE-L",          detail: "Lexical overlap with human-written Nigerian reviews", base: "full 0.119 vs baseline 0.064" },
              { num: "0.925", color: "var(--amber)",    label: "Naija Vibe Score", detail: "Abeg Score on naija-tagged users — cultural authenticity", base: "baseline 0.352 · +163%" },
              { num: "100%",  color: "var(--teal)",     label: "Completion Rate",  detail: "Task B always returns a full recommendation list", base: "zero dropped requests" },
              { num: "0.701", color: "var(--lavender)", label: "Rec Confidence",   detail: "Fingerprint-backed retrieval confidence score", base: "baseline 0.000 — no model" },
            ].map(m => (
              <div key={m.label} className="proof-card" style={{ "--proof-color": m.color }}>
                <div className="proof-num" style={{ color: m.color }}>{m.num}</div>
                <div className="proof-label">{m.label}</div>
                <div className="proof-detail">{m.detail}</div>
                <div className="proof-base">{m.base}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== THE PROBLEM ===== */}
      <section className="section container" aria-label="The Problem">
        <Reveal>
          <div className="eyebrow" style={{ marginBottom: 24 }}>{t.problemLabel || "The Problem"}</div>
        </Reveal>
        <div style={{ display: "flex", flexDirection: "column", gap: 80, maxWidth: 920 }}>
          <Reveal>
            <div className="beat">
              <div className="beat-num">Beat 01</div>
              Every day, <span className="bold">millions of Nigerians</span> leave reviews,
              rate products, and make choices online.
            </div>
          </Reveal>
          <Reveal delay={100}>
            <div className="beat">
              <div className="beat-num">Beat 02</div>
              <span className="quiet">But the AI systems that analyse them? Built on American data, trained on Western patterns, tested on English</span>{" "}
              <span className="bold">that sounds nothing like us.</span>
            </div>
          </Reveal>
          <Reveal delay={200}>
            <div className="beat">
              <div className="beat-num">Beat 03</div>
              A Lagos foodie who writes{" "}
              <span className="tealtxt mono" style={{ fontSize: "0.7em" }}>"this jollof hit different — proper party vibes"</span>{" "}
              gets flattened into the same profile as someone in Ohio who writes{" "}
              <span className="dim mono" style={{ fontSize: "0.7em" }}>"the food was great."</span>
            </div>
          </Reveal>

          <Reveal delay={150}>
            <div className="compare" role="region" aria-label="Comparison: Generic AI vs Naiview">
              <div className="compare-card generic">
                <div className="compare-label">Generic AI</div>
                <p>"The restaurant was good. The food was tasty and the service was acceptable. I would recommend it."</p>
                <div className="row" style={{ marginTop: 16 }}>
                  <Stars value={4} size={14}/>
                  <span className="mono dim" style={{ fontSize: 11 }}>RATING 4.0</span>
                </div>
              </div>
              <div className="compare-card naija">
                <div className="compare-label">Naiview · Naija Vibe Mode</div>
                <p>"Omo, the jollof hit different! Service slow small sha but the food make up for am. For VI price, e dey reasonable. I go come back with my squad."</p>
                <div className="row" style={{ marginTop: 16 }}>
                  <Stars value={4} size={14}/>
                  <span className="mono tealtxt" style={{ fontSize: 11 }}>VIBE 0.84 · CONF 0.87</span>
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={100}>
            <div style={{ textAlign: "center", paddingTop: 24 }}>
              <h2 style={{ fontSize: "clamp(32px,4vw,52px)" }}>
                {t.fixThis || "We decided to"} <span className="tealtxt">{vibe ? "fix am." : "fix this."}</span>
              </h2>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ===== THE SOLUTION ===== */}
      <section className="section container" style={{ paddingTop: 60 }} aria-label="The Solution">
        <Reveal>
          <div className="sec-head">
            <div className="eyebrow">{t.solutionLabel || "The Solution"}</div>
            <h2>The first user modelling system built from the ground up around <span className="lavtxt">Nigerian behavioural patterns</span>.</h2>
            <p className="lede">Two tasks. One culturally-aware agent. Engineered to feel like the people it serves.</p>
          </div>
        </Reveal>

        <div className="sol-cards">
          <Reveal>
            <div className="sol-card" style={{ ["--accent-color"]: "var(--teal)" }}>
              <div className="sol-tag">Task A · User Modeling</div>
              <h3>{tTaskA.title || "Review Generation"}</h3>
              <p className="sol-desc">Persona + product → realistic Nigerian-style review and rating, anchored to a 7-dimensional behavioural fingerprint.</p>
              <div className="sol-preview">
                <div className="mono dim" style={{ fontSize: 10, marginBottom: 6 }}>· OUTPUT PREVIEW</div>
                <div style={{ fontSize: 13, color: "var(--fg)", lineHeight: 1.5 }}>"Abeg, if you never chop for Mama Cass, you never start. The jollof rice hit different..."</div>
                <div className="row" style={{ marginTop: 12, justifyContent: "space-between" }}>
                  <Stars value={4} size={12}/>
                  <span className="chip high"><span className="chip-dot"></span> 0.87</span>
                </div>
              </div>
              <button className="btn btn-sm" style={{ marginTop: 20 }} onClick={() => navigate("/task-a")}>
                {vibe ? "Try Task A →" : "Try Task A →"}
              </button>
            </div>
          </Reveal>
          <Reveal delay={120}>
            <div className="sol-card" style={{ ["--accent-color"]: "var(--amber)" }}>
              <div className="sol-tag">Task B · Recommendations</div>
              <h3>{tTaskB.title || "Smart Recommendations"}</h3>
              <p className="sol-desc">Persona → personalised picks with reasoning in Nigerian voice. Handles cold-start through a 3-turn conversation.</p>
              <div className="sol-preview">
                <div className="mono dim" style={{ fontSize: 10, marginBottom: 6 }}>· TOP MATCH</div>
                <div className="row" style={{ justifyContent: "space-between", alignItems: "start" }}>
                  <div>
                    <div style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}>The Place Restaurant, Lekki</div>
                    <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>FOOD · LAGOS</div>
                  </div>
                  <div style={{ fontFamily: "var(--f-display)", fontSize: 22, color: "var(--amber)" }}>94%</div>
                </div>
              </div>
              <button className="btn btn-sm" style={{ marginTop: 20 }} onClick={() => navigate("/task-b")}>
                {vibe ? "Try Task B →" : "Try Task B →"}
              </button>
            </div>
          </Reveal>
        </div>

        <div className="fp-strip" style={{ ["--accent-color"]: "var(--teal)" }} aria-hidden="true">
          <div className="fp-track">
            {[...FP_DIMS, ...FP_DIMS, ...FP_DIMS].map((d, i) => (
              <div key={i} className="fp-item">
                <span className="fp-dot"></span>
                <span style={{ color: "var(--fg-dim)", fontFamily: "var(--f-mono)", fontSize: 11 }}>{String(i % 7 + 1).padStart(2, "0")}</span>
                <span style={{ textTransform: "uppercase", letterSpacing: "0.14em" }}>{d.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== MANIFESTO ===== */}
      <section className="manifesto" aria-label="Manifesto">
        <div className="container manifesto-grid">
          <Reveal>
            <div className="manifesto-stick">
              <div className="eyebrow" style={{ marginBottom: 16, color: "var(--amber)" }}>{t.manifestoLabel || "Manifesto"}</div>
              <h2>Why culture is <em>architecture</em>, not decoration.</h2>
            </div>
          </Reveal>
          <Reveal delay={100}>
            <div className="manifesto-body">
              <p>
                Nigerian reviewers show a <span className="ambertxt">bimodal rating pattern</span> — 5 stars when happy, 1 star when angry. Western models expect a bell curve. If your AI assumes that curve, it misreads every Nigerian user before it has even read a single word.
              </p>
              <p>
                A Kano user reviewing suya writes completely differently from a Port Harcourt user reviewing seafood. Region isn't metadata — <span className="ambertxt">it's identity</span>. Treat it as a tag and you've already lost the thread.
              </p>
              <p>
                <span className="mono tealtxt" style={{ background: "var(--teal-soft)", padding: "2px 8px", borderRadius: 4, fontSize: 13 }}>"E sweet die"</span>{" "}
                and{" "}
                <span className="mono dim" style={{ background: "var(--bg-elev)", padding: "2px 8px", borderRadius: 4, fontSize: 13 }}>"The food was excellent"</span>{" "}
                carry the same sentiment but wildly different cultural signals. An AI that treats them the same understands neither.
              </p>
              <blockquote className="pull-quote pull-quote-hero">
                We didn't build a recommendation engine and <span>add Nigerian flavour</span>.
                <br/>We built <span>Nigerian intelligence</span> and gave it an engine.
              </blockquote>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ===== TEAM ===== */}
      <section className="section container" aria-label="Team">
        <Reveal>
          <div className="sec-head" style={{ textAlign: "center", margin: "0 auto 16px", alignItems: "center" }}>
            <div className="eyebrow">{t.buildersLabel || "The Builders"}</div>
            <h2>Built by people who get it.</h2>
          </div>
        </Reveal>

        <div className="team-grid">
          {[
            { name: "Testimony", role: "Agent Architecture & ML Engineering", quote: "I wanted to build AI that sounds like the people I grew up with.", color: "var(--teal)" },
            { name: "Aaliyah", role: "Memory Systems & Data Pipeline", quote: "The data gap isn't a limitation — it's an opportunity to be original.", color: "var(--amber)" },
            { name: "Shiloh", role: "Nigerian Language Module & Cultural Research", quote: "If the vibe check fails, we don't ship it.", color: "var(--lavender)" },
          ].map((p, i) => (
            <Reveal key={p.name} delay={i * 100}>
              <div className="team-card" style={{ ["--accent-color"]: p.color }}>
                <Avatar name={p.name} color={p.color} size={96} />
                <div className="team-name">{p.name}</div>
                <div className="team-role">{p.role}</div>
                <div className="team-quote">"{p.quote}"</div>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={200}>
          <div style={{ textAlign: "center", marginTop: 48, color: "var(--fg-mute)", fontSize: 16 }}>
            {t.builtBy || "Three builders. One mission."}{" "}
            <span className="tealtxt">{t.mission || "Make AI that actually gets us."}</span>
          </div>
        </Reveal>
      </section>

      {/* ===== STATS BAR ===== */}
      <section className="section-sm container" aria-label="Project stats">
        <Reveal>
          <div className="stats-bar">
            {[
              { n: "16", l: "LangChain Tools" },
              { n: "12", l: "Agent A Nodes" },
              { n: "14", l: "Agent B Nodes" },
              { n: "7",  l: "Fingerprint Dims" },
              { n: "6",  l: "Eval Metrics" },
            ].map(s => (
              <div key={s.l} className="stat">
                <div className="stat-num">{s.n}</div>
                <div className="stat-label">{s.l}</div>
              </div>
            ))}
          </div>
        </Reveal>
      </section>

      {/* ===== JUDGES PATH ===== */}
      <section className="section-sm container" aria-label="Judges guide">
        <Reveal>
          <div className="judges-path">
            <div className="eyebrow" style={{ marginBottom: 16, textAlign: "center" }}>
              {vibe ? "Judge, this na how to see am" : "Judge's recommended path"}
            </div>
            <div className="judges-steps">
              {[
                { n: "①", label: vibe ? "Toggle Naija Vibe Mode" : "Toggle Naija Vibe Mode", sub: vibe ? "Watch everything switch to Pidgin" : "Watch the whole site switch to Pidgin", color: "var(--amber)" },
                { n: "②", label: vibe ? "Run Quick Scenario" : "Run a Quick Scenario", sub: vibe ? "One click — watch the agent generate" : "One click on Task A — watch the agent think", color: "var(--teal)" },
                { n: "③", label: vibe ? "Check the Architecture" : "Check the Architecture", sub: vibe ? "Click nodes to see what each one do" : "Click nodes to explore what each component does", color: "var(--lavender)" },
              ].map(step => (
                <div key={step.n} className="judges-step">
                  <div className="judges-step-num" style={{ color: step.color }}>{step.n}</div>
                  <div className="judges-step-label">{step.label}</div>
                  <div className="judges-step-sub">{step.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </section>

      {/* ===== CTA ===== */}
      <section className="cta-section container" aria-label="Call to action">
        <Reveal>
          <div className="eyebrow" style={{ marginBottom: 16 }}>{t.tryLabel || "Try it yourself"}</div>
          <h2>Two tasks. <span className="tealtxt">{t.thirtySeconds || "Thirty seconds"}</span> {t.feelDifference || "to feel the difference."}</h2>
          <div className="cta-row">
            <button className="btn btn-primary btn-lg" onClick={() => navigate("/task-a")}>
              {tTaskA.generateBtn || "Generate a Review"} →
            </button>
            <button className="btn btn-amber btn-lg" onClick={() => navigate("/task-b")}>
              {tTaskB.getRecsBtn || "Get Recommendations →"}
            </button>
          </div>
          <div className="cta-links">
            <a href="#/paper" onClick={(e)=>{e.preventDefault();navigate("/paper");}}>
              {vibe ? "Read our Solution Paper ↓" : "Read our Solution Paper ↓"}
            </a>
            <a href="#/architecture" onClick={(e)=>{e.preventDefault();navigate("/architecture");}}>
              {vibe ? "Explore the Architecture →" : "Explore the Architecture →"}
            </a>
            <a href="#/evaluation" onClick={(e)=>{e.preventDefault();navigate("/evaluation");}}>
              {vibe ? "See the Evaluation Numbers →" : "See the Evaluation Numbers →"}
            </a>
          </div>
        </Reveal>
      </section>
    </div>
  );
}

Object.assign(window, { Landing });
