/* TASK B — Recommendation Engine */

const { useState, useEffect, useRef, useCallback } = React;

const DEMO_COLD_START = [
  "Omo, welcome! Quick one — what kind of food do you normally enjoy?",
  "Nice! Are you someone that values taste above everything, or does price/value matter more?",
  "Got you. Last one — do you prefer busy lively spots or quieter places?",
];

const DEMO_COLD_START_EN = [
  "Welcome! Quick question — what kind of food do you normally enjoy?",
  "Great! Do you value taste above everything, or does price/value matter more?",
  "Got it. Last one — do you prefer busy, lively spots or quieter places?",
];

const DEMO_RECS = [
  {
    name: "The Place Restaurant, Lekki",
    cat: "Food · Lagos",
    match: 94,
    confidence: 0.91,
    reason: "Your jollof rating history says you'll love this one. Same price tier as your usual spots, but the portions are bigger.",
    reasonVibe: "Based on your love for jollof and your weekend brunch pattern, this one go sweet you. Portions plenty, price still dey reasonable.",
  },
  {
    name: "Buka Steki, Surulere",
    cat: "Food · Lagos",
    match: 88,
    confidence: 0.86,
    reason: "Budget-friendly with generous portions — matches your value-conscious pattern across 14 prior reviews.",
    reasonVibe: "Budget-friendly and the portions no be small thing. E match your style — quality food without break bank.",
  },
  {
    name: "Nkoyo, Ikoyi",
    cat: "Food · Lagos · Premium",
    match: 82,
    confidence: 0.79,
    reason: "A step up from your usual mid-tier picks. You've rated 3 special-occasion spots highly in the past 6 months.",
    reasonVibe: "Step up from your regular spots — special occasion vibes. You don dey rate premium places high lately, this one fit your level.",
  },
];

const DEMO_TRACE = [
  { step: 1, title: "Pulled user history", detail: "14 prior food reviews · last 90 days" },
  { step: 2, title: "Computed taste vector", detail: "Topic affinity: jollof, grills, Lagos venues" },
  { step: 3, title: "FAISS retrieval", detail: "Top 50 candidates from item index" },
  { step: 4, title: "Cultural rerank", detail: "Boosted Naija-tone matches · diversity constraint applied" },
  { step: 5, title: "Generated reasoning", detail: "Register selected by vibe mode" },
];

function RecsOutput({ recs, trace, vibe, diversity, onRefresh, t }) {
  return (
    <>
      <div className="between">
        <div>
          <h3 style={{ fontSize: 20 }}>{recs.length} {t.picksLabel || "Personalised Picks"}</h3>
          <div className="dim" style={{ fontSize: 13, marginTop: 4 }}>
            {t.diversityScore || "Diversity score:"}{" "}
            <span className="mono tealtxt">{(diversity || 0.74).toFixed(2)}</span>
            {t.crossCategory || " · Cross-category coverage"}
          </div>
        </div>
        {onRefresh && (
          <button className="btn btn-sm" onClick={onRefresh} aria-label="Refresh recommendations">
            {t.refreshBtn || "↻ Refresh"}
          </button>
        )}
      </div>

      {recs.map((r, i) => (
        <div
          key={i}
          className="rec-card"
          style={{ animation: `float-in 0.4s ease ${i * 100}ms both` }}
        >
          <div>
            <div className="rec-cat">#{String(i+1).padStart(2,"0")} · {r.cat || r.category || ""}</div>
            <h4>{r.name}</h4>
            <div className="rec-reason">
              {vibe ? (r.reasonVibe || r.explanation || r.reason) : (r.reason || r.explanation)}
            </div>
            <div style={{ marginTop: 12 }}>
              <ConfidenceChip value={r.confidence}/>
            </div>
          </div>
          <div className="rec-match" aria-label={`${r.match || Math.round((r.match_score || 0))}% match`}>
            <div className="pct" style={{
              color: (r.match || r.match_score) >= 90 ? "var(--teal)"
                   : (r.match || r.match_score) >= 85 ? "var(--amber)"
                   : "var(--lavender)",
            }}>
              {r.match || Math.round(r.match_score || 0)}%
            </div>
            <div className="label">MATCH</div>
          </div>
        </div>
      ))}

      {/* Diversity viz */}
      <div className="card" style={{ marginTop: 8 }}>
        <div className="between" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 16 }}>{t.diversityLabel || "Recommendation Diversity"}</h3>
          <span className="mono tealtxt" style={{ fontSize: 14 }}>
            {(diversity || 0.74).toFixed(2)} / 1.00
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {[
            { k: "Price Range", v: 0.82 },
            { k: "Cuisine Variety", v: 0.68 },
            { k: "Region Spread", v: 0.71 },
          ].map(d => (
            <div key={d.k}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                <span className="mono dim" style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase" }}>{d.k}</span>
                <span className="mono" style={{ fontSize: 12, color: "var(--teal)" }}>{d.v.toFixed(2)}</span>
              </div>
              <div style={{ height: 4, background: "var(--bg-elev)", borderRadius: 2, overflow: "hidden" }} role="progressbar" aria-valuenow={d.v * 100} aria-valuemin={0} aria-valuemax={100}>
                <div style={{ width: `${d.v*100}%`, height: "100%", background: "var(--teal)", boxShadow: "0 0 8px var(--teal-glow)", transition: "width 1s ease" }}></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reasoning trace */}
      {trace && trace.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 16, marginBottom: 16 }}>{t.howWeGotHere || "How we got here"}</h3>
          <div className="trace">
            {trace.map((s, i) => (
              <div key={i} className="trace-step done">
                <div className="trace-num" aria-hidden="true">{String(s.step || i+1).padStart(2,"0")}</div>
                <div className="trace-body">
                  <div className="trace-title">{s.title}</div>
                  <div className="trace-detail">
                    {s.detail || (vibe ? "Pidgin register · slang index 0.74" : "Standard English register")}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

const REC_SCENARIOS = [
  { id: "lagos-food",  chip: "Lagos Foodie",     persona: "ChiomaNwankwo92", category: "Food",          mood: "somewhere lively for Saturday night with my squad in Lagos" },
  { id: "abuja-tech",  chip: "Abuja Tech Buyer",  persona: "AdekunleRoads",   category: "Electronics",   mood: "latest smartphone or laptop under ₦500k, best value" },
  { id: "ph-books",    chip: "PH Book Lover",     persona: "FunkeAdebayo",    category: "Books",         mood: "something deep, Nigerian, that hits different" },
  { id: "lagos-exp",   chip: "Lagos Experience",  persona: "EmekaLagosBoy",   category: "Entertainment", mood: "premium experience for a special occasion, Ikoyi or VI" },
];

function TaskB({ vibe, setVibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).taskB || {};

  const [mode, setMode] = useState("existing");
  const [persona, setPersona] = useState("");
  const [mood, setMood] = useState("");
  const [category, setCategory] = useState("Food");

  const [recs, setRecs] = useState(null);
  const [diversityScore, setDiversityScore] = useState(null);
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Cold start
  const [chatLog, setChatLog] = useState([]);
  const [turn, setTurn] = useState(0);
  const [userInput, setUserInput] = useState("");
  const [agentTyping, setAgentTyping] = useState(false);
  const chatRef = useRef(null);

  const coldStartQuestions = vibe ? DEMO_COLD_START : DEMO_COLD_START_EN;

  const startColdStart = useCallback(() => {
    setChatLog([]);
    setTurn(0);
    setRecs(null);
    setTrace(null);
    setError(null);
    setAgentTyping(true);
    setTimeout(() => {
      setChatLog([{ role: "agent", text: coldStartQuestions[0] }]);
      setAgentTyping(false);
    }, 700);
  }, [vibe]);

  useEffect(() => {
    if (mode === "coldstart" && chatLog.length === 0) startColdStart();
  }, [mode]);

  // Re-start cold start when vibe mode changes mid-conversation
  useEffect(() => {
    if (mode === "coldstart" && chatLog.length > 0) {
      const updated = chatLog.map((m, i) => {
        if (m.role === "agent" && i < coldStartQuestions.length) {
          return { ...m, text: coldStartQuestions[Math.floor(i / 2)] };
        }
        return m;
      });
      setChatLog(updated);
    }
  }, [vibe]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [chatLog, agentTyping]);

  const sendUserMessage = useCallback(async () => {
    if (!userInput.trim()) return;
    const newLog = [...chatLog, { role: "user", text: userInput }];
    setChatLog(newLog);
    setUserInput("");
    const nextTurn = turn + 1;

    setAgentTyping(true);

    if (nextTurn < coldStartQuestions.length) {
      setTimeout(() => {
        setChatLog([...newLog, { role: "agent", text: coldStartQuestions[nextTurn] }]);
        setTurn(nextTurn);
        setAgentTyping(false);
      }, 1100);
    } else {
      const doneMsg = vibe
        ? "Perfect, I don get your vibe. E dey generate recommendations now..."
        : "Perfect, I've got your vibe. Generating recommendations now...";
      setTimeout(async () => {
        setChatLog([...newLog, { role: "agent", text: doneMsg }]);
        setTurn(nextTurn);
        setAgentTyping(false);

        if (window.isDemoMode && window.isDemoMode()) {
          await new Promise(r => setTimeout(r, 900));
          setRecs(DEMO_RECS);
          setTrace(DEMO_TRACE);
          setDiversityScore(0.74);
        } else {
          try {
            const data = await window.apiPost("/task-b/cold-start", {
              session_id: sessionStorage.getItem("naiview-session") || Math.random().toString(36).slice(2),
              turn_number: nextTurn,
              naija_vibe_mode: vibe,
            });
            if (data.done && data.recommendations) {
              setRecs(data.recommendations);
              setTrace(data.reasoning_trace || []);
              setDiversityScore(data.diversity_score);
            }
          } catch (err) {
            setError(err.message || "Unknown error");
          }
        }
      }, 1100);
    }
  }, [chatLog, turn, userInput, vibe, coldStartQuestions]);

  const generateRecs = useCallback(async () => {
    setLoading(true);
    setRecs(null);
    setTrace(null);
    setError(null);

    const payload = {
      naija_vibe_mode: vibe,
      category,
      mood: mood || undefined,
      persona,
    };

    if (window.isDemoMode && window.isDemoMode()) {
      await new Promise(r => setTimeout(r, 900));
      setRecs(DEMO_RECS);
      setTrace(DEMO_TRACE);
      setDiversityScore(0.74);
      setLoading(false);
      return;
    }

    try {
      const data = await window.apiPost("/task-b/recommend", payload);
      setRecs(data.recommendations || []);
      setTrace(data.reasoning_trace || []);
      setDiversityScore(data.diversity_score);
    } catch (err) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [vibe, category, mood, persona]);

  return (
    <div className="page container" style={{ paddingTop: 100, paddingBottom: 80 }}>
      <div className="sec-head" style={{ marginBottom: 32 }}>
        <div className="eyebrow ambertxt">{t.eyebrow || "Task B · Recommendation Engine"}</div>
        <h1 style={{ fontSize: "clamp(36px,4.6vw,56px)" }}>{t.title || "Get Recommendations"}</h1>
        <p className="lede">{t.description || "Personalised picks with reasoning in Nigerian voice. No prior history? The agent runs a 3-turn warm-up chat to learn your taste."}</p>
      </div>

      {/* Quick-fill scenario chips */}
      <div className="scenario-chips" style={{ marginBottom: 24 }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>
          {vibe ? "Quick scenarios — click to load am" : "Quick scenarios — one click to load"}
        </div>
        <div className="scenario-chip-row">
          {REC_SCENARIOS.map(sc => (
            <button key={sc.id}
              className={`scenario-chip ${persona === sc.persona && category === sc.category ? "active" : ""}`}
              onClick={() => { setPersona(sc.persona); setCategory(sc.category); setMood(sc.mood); setMode("existing"); setRecs(null); setTrace(null); }}>
              <div className="scenario-chip-label">{sc.chip}</div>
              <div className="scenario-chip-sub">{sc.category}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Mode switcher */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }} role="tablist" aria-label="User mode">
        <button
          role="tab"
          className={`btn ${mode === "existing" ? "btn-primary" : ""}`}
          aria-selected={mode === "existing"}
          onClick={() => { setMode("existing"); setError(null); }}
        >
          {t.existingUserBtn || "Existing User"}
        </button>
        <button
          role="tab"
          className={`btn ${mode === "coldstart" ? "btn-amber" : ""}`}
          aria-selected={mode === "coldstart"}
          onClick={() => { setMode("coldstart"); setError(null); }}
        >
          {t.coldStartBtn || "Cold-Start (no history)"}
        </button>
      </div>

      {mode === "existing" ? (
        <div className="workbench">
          {/* ── INPUT PANEL ── */}
          <div className="panel panel-sticky">
            <div className="panel-title">
              <h3>{t.inputPanelTitle || "Input"}</h3>
              <span className="step">USER · KNOWN</span>
            </div>
            <div className="form-group">
              <label className="label" htmlFor="user-id-b">{t.userIdLabel || "User ID or persona"}</label>
              <input id="user-id-b" className="input mono" value={persona} onChange={(e) => setPersona(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="label" htmlFor="category-select">{t.categoryLabel || "Category"}</label>
              <select id="category-select" className="select" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option>Food</option>
                <option>Electronics</option>
                <option>Books</option>
                <option>Entertainment</option>
                <option>Fashion</option>
                <option>Travel</option>
              </select>
            </div>
            <div className="form-group">
              <label className="label" htmlFor="mood-input">
                {t.moodLabel || "What are you in the mood for?"}{" "}
                <span className="dim" style={{ textTransform: "none", letterSpacing: 0 }}>
                  {t.moodOptional || "(optional)"}
                </span>
              </label>
              <textarea
                id="mood-input"
                className="textarea"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                placeholder={vibe ? "e.g. somewhere lively for Saturday night" : "e.g. somewhere lively for Saturday night"}
              />
            </div>

            <div className="vibe-row">
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{t.vibeModeLabel || "Naija Vibe Mode"}</div>
                <div className="dim" style={{ fontSize: 12 }}>
                  {vibe ? (t.vibeModeOn || "Reasoning in Pidgin") : (t.vibeModeOff || "Standard reasoning")}
                </div>
              </div>
              <NaijaVibeToggle vibe={vibe} setVibe={setVibe} label=""/>
            </div>

            <button
              className="btn btn-primary"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={generateRecs}
              disabled={loading}
              aria-busy={loading}
            >
              {loading
                ? <span className="mono cursor">{t.loadingBtn || "Finding picks..."}</span>
                : t.getRecsBtn || "Get Recommendations →"
              }
            </button>

            {error && (
              <ErrorBanner
                message={error}
                label={t.errorLabel || "Recommendation failed"}
                onRetry={generateRecs}
              />
            )}
          </div>

          {/* ── OUTPUT ── */}
          <div className="col" style={{ gap: 16 }} aria-live="polite">
            {recs ? (
              <RecsOutput
                recs={recs}
                trace={trace || DEMO_TRACE}
                vibe={vibe}
                diversity={diversityScore}
                onRefresh={generateRecs}
                t={t}
              />
            ) : loading ? (
              <div className="col" style={{ gap: 16 }}>
                {[1,2,3].map(i => (
                  <div key={i} className="rec-card" style={{ opacity: 0.5 }}>
                    <div className="col" style={{ gap: 8 }}>
                      <SkeletonLine width="40%" height={11} />
                      <SkeletonLine width="70%" height={18} />
                      <SkeletonLine width="90%" height={13} />
                      <SkeletonLine width="80%" height={13} />
                    </div>
                    <div className="rec-match">
                      <SkeletonLine width={48} height={28} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="card" style={{ minHeight: 320, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--fg-faint)", textAlign: "center", padding: 40 }}>
                <div>
                  <div className="mono dim" style={{ fontSize: 12, letterSpacing: "0.14em", textTransform: "uppercase", marginBottom: 12 }}>
                    {t.readyTitle || "READY"}
                  </div>
                  <div style={{ fontSize: 16, maxWidth: 360, lineHeight: 1.6 }}>
                    {t.readyDesc1 || "Provide a persona on the left and press"}{" "}
                    <span className="tealtxt">{t.readyDesc2 || "Get Recommendations"}</span>{" "}
                    {t.readyDesc3 || "to see personalised picks with reasoning."}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ── COLD START FLOW ── */
        <div className="workbench">
          <div className="panel panel-sticky">
            <div className="panel-title">
              <h3>{t.warmupTitle || "Warm-up Chat"}</h3>
              <span className="step">{Math.min(turn + 1, 3)} / 3</span>
            </div>
            <p className="dim" style={{ fontSize: 13, marginBottom: 20 }}>
              {t.warmupDesc || "No history yet. The agent runs a quick 3-turn chat to learn your taste, then drops personalised picks."}
            </p>

            {/* Progress bar */}
            <div className="cold-start-progress" role="progressbar" aria-valuenow={Math.min(turn, 3)} aria-valuemin={0} aria-valuemax={3} aria-label={`Turn ${Math.min(turn + 1, 3)} of 3`}>
              {[0,1,2].map(i => (
                <div key={i} className={`progress-seg ${turn > i ? "done" : turn === i ? "active" : ""}`}></div>
              ))}
            </div>
            <div className="mono dim" style={{ fontSize: 12, marginTop: 8, marginBottom: 16 }}>
              Turn {Math.min(turn + 1, 3)} of 3 · {turn >= 3 ? "Complete" : "In progress"}
            </div>

            <div className="divider"></div>

            <div className="vibe-row">
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{t.vibeModeLabel || "Naija Vibe Mode"}</div>
                <div className="dim" style={{ fontSize: 12 }}>
                  {vibe ? (t.vibeModeAgentLabel || "Agent speaks Pidgin") : (t.vibeModeOff || "Standard English")}
                </div>
              </div>
              <NaijaVibeToggle vibe={vibe} setVibe={setVibe} label=""/>
            </div>

            <button
              className="btn btn-sm"
              onClick={startColdStart}
              style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            >
              {t.restartBtn || "↻ Restart Conversation"}
            </button>

            {error && (
              <ErrorBanner
                message={error}
                label={t.errorLabel || "Recommendation failed"}
                onRetry={startColdStart}
              />
            )}
          </div>

          <div className="col" style={{ gap: 20 }}>
            <div className="chat" ref={chatRef} aria-label="Conversation" aria-live="polite">
              {chatLog.length === 0 && !agentTyping && (
                <div style={{ color: "var(--fg-faint)", textAlign: "center", margin: "auto", fontSize: 14 }}>
                  Conversation will start here.
                </div>
              )}
              {chatLog.map((m, i) => (
                <div key={i} className={`bubble ${m.role}`}>{m.text}</div>
              ))}
              {agentTyping && (
                <div className="bubble agent typing" aria-label="Agent is typing">
                  <span className="dot"></span><span className="dot"></span><span className="dot"></span>
                </div>
              )}
            </div>

            {turn < 3 && (
              <div className="chat-input-row">
                <label className="sr-only" htmlFor="chat-input">Your response</label>
                <input
                  id="chat-input"
                  className="input"
                  placeholder={t.inputPlaceholder || "Type your response..."}
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !agentTyping && sendUserMessage()}
                  disabled={agentTyping}
                  aria-disabled={agentTyping}
                />
                <button
                  className="btn btn-primary"
                  onClick={sendUserMessage}
                  disabled={agentTyping || !userInput.trim()}
                  aria-disabled={agentTyping || !userInput.trim()}
                >
                  {t.sendBtn || "Send"}
                </button>
              </div>
            )}

            {recs && (
              <div className="col fade-in" style={{ gap: 16 }} aria-live="polite">
                <div>
                  <h3 style={{ fontSize: 20 }}>{t.coldStartResult || "Based on our chat, here's what I recommend:"}</h3>
                  <div className="dim" style={{ fontSize: 13, marginTop: 4 }}>
                    {t.coldStartResultSub || "Built from 3 turns of warm-up conversation"}
                  </div>
                </div>
                <RecsOutput
                  recs={recs}
                  trace={trace || DEMO_TRACE}
                  vibe={vibe}
                  diversity={diversityScore}
                  onRefresh={null}
                  t={t}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { TaskB });
