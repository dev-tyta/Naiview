/* TASK A — Review Generation Interface */

const { useState, useEffect, useCallback, useRef } = React;

/* ================================================================
   Demo scenarios — 4 cities, 4 categories, distinct fingerprints
================================================================ */
const SCENARIOS = [
  {
    id: "lagos-food", chip: "Lagos Foodie", sub: "Mama Cass · Restaurant",
    inputMode: "persona",
    persona: "A picky Lagos foodie who loves jollof rice, grilled meat, and weekend brunches on VI. Reviews honestly — expects good portions for the price. Biased toward local flavour.",
    userId: "ChiomaNwankwo92",
    itemName: "Mama Cass Restaurant",
    itemCategory: "Restaurant · Lagos VI",
    itemDesc: "Popular Nigerian buffet on Victoria Island. Known for jollof rice, grilled fish, and egusi soup. Mid-range pricing.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.72 },
      { key: "verbosity",  label: "Verbosity",           value: 0.45 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.81 },
      { key: "topic",      label: "Topic Focus",         value: 0.69 },
      { key: "consistency",label: "Consistency",         value: 0.88 },
      { key: "recency",    label: "Recency Weight",       value: 0.65 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.78 },
    ],
    reviewVibe: `Abeg, if you never chop for Mama Cass, you never start. The jollof rice hit different — proper party jollof vibes, that smoky bottom-pot taste. Service slow small sha, but food make up for am. For VI price, e dey very reasonable. I go come back with my squad next weekend. 4 stars because that AC need to work harder!`,
    reviewEn: `Had a pleasant meal at Mama Cass Restaurant on Victoria Island. The jollof rice was flavorful and well-prepared with a good smoky depth. Service could have been faster. Pricing was reasonable for the area. Air conditioning was inadequate. Would consider returning.`,
    rating: 4.0, confidence: 0.87, vibeScore: 0.84,
    fingerprintMatch: "High — frequent reviewer of grills and street food, Lagos-Abuja corridor",
    styleNotes: "Short, punchy reviews. Direct opinions on food quality and price-value.",
    reasoning: [
      { step: 1, title: "User identified: Lagos foodie",       detail: "VI/Lekki corridor signals · 14 similar restaurant reviews last 90 days" },
      { step: 2, title: "Category match: 94%",                 detail: "Nigerian cuisine, mid-range — strong fingerprint alignment on food affinity" },
      { step: 3, title: "Region detected: Lagos",              detail: "VI, Lekki, danfo signals · region confidence 0.89" },
      { step: 4, title: "Sentiment predicted: Positive 4.0–4.5", detail: "Category affinity + price-tier comfort score → positive prior" },
      { step: 5, title: "Pidgin register applied",             detail: "Naija slang index target 0.78 · Lagos VI register with local food terms" },
      { step: 6, title: "Vibe Check: 0.84 ✓",                 detail: "cultural_authenticity 0.86 · cultural_accuracy 0.82 · persona_consistency 0.85" },
    ],
  },
  {
    id: "abuja-tech", chip: "Abuja Tech", sub: "iPhone 15 Pro · Electronics",
    inputMode: "persona",
    persona: "An Abuja-based tech enthusiast, late 20s, FCT corridor. Compares every device to Apple. High expectations, notices small details. Price-sensitive given naira fluctuations. Writes detailed reviews.",
    userId: "AdekunleRoads",
    itemName: "iPhone 15 Pro Max",
    itemCategory: "Electronics · Smartphone · Premium",
    itemDesc: "Apple flagship 2023. 48MP main camera, titanium build, A17 Pro chip, USB-C. Retails ~₦850,000 in Nigeria.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.61 },
      { key: "verbosity",  label: "Verbosity",           value: 0.82 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.58 },
      { key: "topic",      label: "Topic Focus",         value: 0.75 },
      { key: "consistency",label: "Consistency",         value: 0.91 },
      { key: "recency",    label: "Recency Weight",       value: 0.72 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.55 },
    ],
    reviewVibe: `Guy, this iPhone 15 Pro Max na serious investment — 850k no be small change for this economy. But e worth am? Camera? E dey mad — portrait mode for Nigerian indoor lighting perform well well. Titanium body feel premium. Only wahala be say if you fall am, your heart go pain you. If you get the money comfortably, add am. If you dey manage, stay with your 13 Pro small.`,
    reviewEn: `The iPhone 15 Pro Max is a significant upgrade. The 48MP camera performs well in Nigerian indoor and outdoor conditions. The titanium build feels premium and substantial. The A17 Pro chip handles everything smoothly. At ₦850,000 in the current economic climate, it is a serious financial decision, but the performance justifies the premium for power users.`,
    rating: 4.5, confidence: 0.89, vibeScore: 0.79,
    fingerprintMatch: "High — tech reviewer, Abuja corridor, premium products with economic price context",
    styleNotes: "Detailed, comparative. Strong naira price sensitivity. Always references economic context.",
    reasoning: [
      { step: 1, title: "User identified: Abuja tech reviewer",  detail: "Wuse, Maitama, FCT signals · 21 prior electronics reviews" },
      { step: 2, title: "Category match: 91%",                   detail: "Electronics, premium tier — matches price-tier behaviour from history" },
      { step: 3, title: "Region detected: Abuja",                detail: "Wuse, Maitama, Garki signals · region confidence 0.84" },
      { step: 4, title: "Price sensitivity flag triggered",       detail: "User consistently references naira conversion rate in 78% of reviews" },
      { step: 5, title: "Register: mixed Pidgin-English",         detail: "Naija slang index 0.55 — semi-formal with Pidgin emphasis markers" },
      { step: 6, title: "Vibe Check: 0.79 ✓",                   detail: "cultural_authenticity 0.76 · cultural_accuracy 0.84 · persona_consistency 0.78" },
    ],
  },
  {
    id: "kano-suya", chip: "Kano Suya Expert", sub: "Wazobia Spot · Street Food",
    inputMode: "persona",
    persona: "A Kano local who takes suya seriously. Rates on marinade, char level, tenderness, yaji blend, and authenticity. Direct and no-nonsense. Won't give false stars — harsh on lazy suya.",
    userId: "MalamIbrahimKano",
    itemName: "Wazobia Suya Spot",
    itemCategory: "Street Food · Suya · Kano",
    itemDesc: "Roadside suya spot in Sabon Gari, Kano. Ram suya and liver. Family-run since 1998. Charcoal grill only.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.88 },
      { key: "verbosity",  label: "Verbosity",           value: 0.38 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.65 },
      { key: "topic",      label: "Topic Focus",         value: 0.95 },
      { key: "consistency",label: "Consistency",         value: 0.94 },
      { key: "recency",    label: "Recency Weight",       value: 0.58 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.71 },
    ],
    reviewVibe: `Wazobia sabi their work, no cap. Ram suya tender, yaji dey balanced — spice dey there but no go kill you. Liver fresh, not that frozen rubbish. This na authentic Kano suya, not that watered-down Lagos version wey dey miss the point. If you pass Sabon Gari, follow your nose — smoke go lead you there. 5 stars, wallahi.`,
    reviewEn: `Wazobia delivers authentic Kano-style suya. The ram suya is tender with appropriate charring. The yaji blend is well-calibrated — present heat without overpowering the meat. The liver cuts are fresh, not frozen. This is traditional suya prepared correctly with consistent quality. A genuine Sabon Gari institution.`,
    rating: 5.0, confidence: 0.93, vibeScore: 0.93,
    fingerprintMatch: "Very high — expert street food reviewer, strong Kano regional identity, 28 suya-specific reviews",
    styleNotes: "Direct expert assessments. Short but precise. Zero tolerance for inauthenticity.",
    reasoning: [
      { step: 1, title: "User identified: Kano suya expert",    detail: "Sabon Gari, Hausa loanwords, suya-specific vocabulary · 28 suya reviews" },
      { step: 2, title: "Category match: 98%",                  detail: "Suya, street food, Kano — exact match for user's primary review domain" },
      { step: 3, title: "Region detected: Kano",                detail: "Sabon Gari, ranka dede, suya terms · region confidence 0.97" },
      { step: 4, title: "Sentiment predicted: Very Positive",   detail: "Authentic Kano charcoal suya — this user's highest-rated category pattern" },
      { step: 5, title: "Hausa register + Kano Pidgin applied", detail: "Naija slang index 0.71 · Hausa loanwords: wallahi, madalla injected by NLM" },
      { step: 6, title: "Vibe Check: 0.93 ✓ STRONG",           detail: "cultural_authenticity 0.95 · cultural_accuracy 0.94 · persona_consistency 0.90" },
    ],
  },
  {
    id: "ph-book", chip: "PH Literature", sub: "Things Fall Apart · Book",
    inputMode: "persona",
    persona: "A Port Harcourt literature teacher and avid reader. Reviews books with cultural depth, compares against African literature canon. Notices when books represent communities authentically vs through colonial lens.",
    userId: "FunkeAdebayo",
    itemName: "Things Fall Apart",
    itemCategory: "Book · African Literature · Classic",
    itemDesc: "Chinua Achebe, 1958. Pre-colonial Igbo society and its clash with European colonialism. Most-read African novel. Igbo cultural systems depicted from the inside.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.79 },
      { key: "verbosity",  label: "Verbosity",           value: 0.87 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.73 },
      { key: "topic",      label: "Topic Focus",         value: 0.84 },
      { key: "consistency",label: "Consistency",         value: 0.92 },
      { key: "recency",    label: "Recency Weight",       value: 0.61 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.63 },
    ],
    reviewVibe: `I read this book again and e still hit me like the first time. Achebe no dey play — every chapter you go feel say na your grandfather dey talk. The way e capture the chi concept, the ozo title, the clan judgment — e no be Western interpretation, e be insider knowledge. For Naija reader, this book pass book, e be like family history. If you never read am, abeg start today. 5 stars no be enough.`,
    reviewEn: `Rereading Things Fall Apart confirms why it remains essential literature. Achebe renders pre-colonial Igbo society with cultural authority — the hierarchies, spiritual systems, and community structures feel authentic rather than anthropological. The novel's power is that Achebe writes his own people from the inside. Every Nigerian should read this at least twice.`,
    rating: 5.0, confidence: 0.94, vibeScore: 0.88,
    fingerprintMatch: "Very high — cultural reviewer, consistent 5-star for culturally resonant works, Igbo cultural affinity markers",
    styleNotes: "Articulate, analytical reviews with cultural specificity. References cultural concepts directly.",
    reasoning: [
      { step: 1, title: "User identified: PH cultural reviewer", detail: "GRA, Trans Amadi signals · Igbo loanwords (biko, nna) · 19 lit reviews avg 4.7★" },
      { step: 2, title: "Category match: 97%",                  detail: "African literature, cultural resonance — exact match for user's highest-affinity category" },
      { step: 3, title: "Region detected: Port Harcourt",       detail: "GRA, Trans Amadi, bole, Garden City signals · region confidence 0.88" },
      { step: 4, title: "Igbo cultural markers identified",     detail: "biko, nna, Igbo-language tokens in user history — code-switch patterns mapped" },
      { step: 5, title: "Register: educated Pidgin blend",      detail: "Naija slang index 0.63 · formal English + Pidgin cultural emphasis markers" },
      { step: 6, title: "Vibe Check: 0.88 ✓",                  detail: "cultural_authenticity 0.91 · cultural_accuracy 0.87 · persona_consistency 0.86" },
    ],
  },
];

const FP_LABELS = {
  generosity: "Generosity", verbosity: "Verbosity",
  emotion: "Emotional Intensity", topic: "Topic Focus",
  consistency: "Consistency", recency: "Recency Weight", naija: "Naija Slang Index",
};

/* ================================================================
   CopyButton
================================================================ */
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).catch(() => {
      const el = document.createElement("textarea");
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    });
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };
  return (
    <button className="btn btn-sm copy-btn" onClick={copy} title="Copy review to clipboard"
            style={{ color: copied ? "var(--teal)" : "var(--fg-mute)", borderColor: copied ? "var(--teal)" : "var(--border)" }}>
      {copied ? (
        <><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg> Copied</>
      ) : (
        <><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</>
      )}
    </button>
  );
}

/* ================================================================
   Main TaskA component
================================================================ */
function TaskA({ vibe, setVibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).taskA || {};

  const [activeScenario, setActiveScenario] = useState(null);
  const [inputMode, setInputMode] = useState("persona");
  const [userId, setUserId] = useState("");
  const [persona, setPersona] = useState("");
  const [itemName, setItemName] = useState("");
  const [itemCategory, setItemCategory] = useState("");
  const [itemDesc, setItemDesc] = useState("");

  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [traceOpen, setTraceOpen] = useState(true);
  const [typed, setTyped] = useState("");
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [error, setError] = useState(null);
  const outputRef = useRef(null);

  // Load scenario
  const loadScenario = useCallback((sc) => {
    setActiveScenario(sc.id);
    setInputMode(sc.inputMode);
    setUserId(sc.userId);
    setPersona(sc.persona);
    setItemName(sc.itemName);
    setItemCategory(sc.itemCategory);
    setItemDesc(sc.itemDesc);
    setResult(null);
    setTyped("");
    setError(null);
    setVisibleSteps(0);
  }, []);

  // Run a scenario immediately (chip one-click)
  const runScenario = useCallback(async (sc) => {
    loadScenario(sc);
    // slight delay so state settles
    await new Promise(r => setTimeout(r, 80));

    setGenerating(true);
    setResult(null);
    setTyped("");
    setError(null);
    setVisibleSteps(0);

    const payload = {
      naija_vibe_mode: vibe,
      item_metadata: { name: sc.itemName, category: sc.itemCategory, description: sc.itemDesc },
      ...(sc.inputMode === "user" ? { user_id: sc.userId } : { persona: sc.persona }),
    };

    if (window.isDemoMode && window.isDemoMode()) {
      await new Promise(r => setTimeout(r, 1100));
      setResult({
        review_text: vibe ? sc.reviewVibe : sc.reviewEn,
        rating: sc.rating,
        confidence: sc.confidence,
        vibe_score: sc.vibeScore,
        fingerprint: sc.fingerprint.map(d => ({ dimension: d.key, value: d.value })),
        fingerprint_match: sc.fingerprintMatch,
        style_notes: sc.styleNotes,
        reasoning_trace: sc.reasoning,
      });
      setGenerating(false);
      // Scroll to output on mobile
      setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 200);
      return;
    }

    try {
      const data = await window.apiPost("/task-a/generate", payload);
      setResult(data);
      setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 200);
    } catch (err) {
      setError(err.message || "Unknown error");
    } finally {
      setGenerating(false);
    }
  }, [vibe]);

  // Manual generate (form-based)
  const generate = useCallback(async () => {
    setGenerating(true);
    setResult(null);
    setTyped("");
    setError(null);
    setVisibleSteps(0);

    const sc = SCENARIOS.find(s => s.id === activeScenario);
    const payload = {
      naija_vibe_mode: vibe,
      item_metadata: { name: itemName, category: itemCategory, description: itemDesc },
      ...(inputMode === "user" ? { user_id: userId } : { persona }),
    };

    if (window.isDemoMode && window.isDemoMode()) {
      await new Promise(r => setTimeout(r, 1100));
      setResult({
        review_text: sc ? (vibe ? sc.reviewVibe : sc.reviewEn) : (vibe
          ? "Abeg, this one hit different sha. E get that authentic Nigerian vibes wey you dey look for. Service dey okay, price reasonable. I fit recommend am."
          : "A solid experience overall. The quality meets expectations and pricing is fair. Would recommend to others looking for this category."),
        rating: sc ? sc.rating : 4.0,
        confidence: sc ? sc.confidence : 0.81,
        vibe_score: sc ? sc.vibeScore : 0.76,
        fingerprint: sc ? sc.fingerprint.map(d => ({ dimension: d.key, value: d.value }))
          : [{ dimension: "generosity", value: 0.65 }, { dimension: "verbosity", value: 0.50 }, { dimension: "emotion", value: 0.70 }, { dimension: "topic", value: 0.60 }, { dimension: "consistency", value: 0.80 }, { dimension: "recency", value: 0.60 }, { dimension: "naija", value: 0.65 }],
        fingerprint_match: sc ? sc.fingerprintMatch : "Moderate — insufficient history for high-confidence match",
        style_notes: sc ? sc.styleNotes : "Mixed verbosity pattern detected",
        reasoning_trace: sc ? sc.reasoning : [
          { step: 1, title: "User history loaded", detail: "Custom persona provided" },
          { step: 2, title: "Fingerprint computed", detail: "7 dimensions calculated from available signals" },
          { step: 3, title: "Region inferred", detail: "Signals detected from persona text" },
          { step: 4, title: "Draft generated", detail: vibe ? "Pidgin register selected" : "Standard English register" },
          { step: 5, title: "Vibe Check completed", detail: "Score within acceptable range" },
        ],
      });
      setGenerating(false);
      setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 200);
      return;
    }

    try {
      const data = await window.apiPost("/task-a/generate", payload);
      setResult(data);
      setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 200);
    } catch (err) {
      setError(err.message || "Unknown error");
    } finally {
      setGenerating(false);
    }
  }, [vibe, inputMode, userId, persona, itemName, itemCategory, itemDesc, activeScenario]);

  // Typewriter effect
  useEffect(() => {
    if (!result?.review_text) return;
    let i = 0;
    setTyped("");
    const id = setInterval(() => {
      i += 3;
      setTyped(result.review_text.slice(0, i));
      if (i >= result.review_text.length) clearInterval(id);
    }, 14);
    return () => clearInterval(id);
  }, [result?.review_text]);

  // Animated trace steps
  useEffect(() => {
    if (!result) { setVisibleSteps(0); return; }
    const steps = (result.reasoning_trace || []).length;
    setVisibleSteps(0);
    let current = 0;
    const iv = setInterval(() => {
      current += 1;
      setVisibleSteps(current);
      if (current >= steps) clearInterval(iv);
    }, 220);
    return () => clearInterval(iv);
  }, [result]);

  const radarData = result?.fingerprint
    ? result.fingerprint.map(d => ({ key: d.dimension, label: FP_LABELS[d.dimension] || d.dimension, value: d.value }))
    : (SCENARIOS.find(s => s.id === activeScenario)?.fingerprint || SCENARIOS[0].fingerprint);

  const reasoningSteps = result?.reasoning_trace || [];

  return (
    <div className="page container" style={{ paddingTop: 100, paddingBottom: 80 }}>
      <div className="sec-head" style={{ marginBottom: 24 }}>
        <div className="eyebrow tealtxt">{t.eyebrow || "Task A · User Modeling"}</div>
        <h1 style={{ fontSize: "clamp(36px,4.6vw,56px)" }}>{t.title || "Generate a Review"}</h1>
        <p className="lede">{t.description || "Feed the agent a persona and a product. Watch a culturally-grounded review come back with a full reasoning trace."}</p>
      </div>

      {/* ── Quick-fill scenario chips ── */}
      <div className="scenario-chips">
        <div className="eyebrow" style={{ marginBottom: 10 }}>
          {vibe ? "Quick scenarios — click to run am" : "Quick scenarios — one click to run"}
        </div>
        <div className="scenario-chip-row">
          {SCENARIOS.map(sc => (
            <button key={sc.id} onClick={() => runScenario(sc)}
              className={`scenario-chip ${activeScenario === sc.id ? "active" : ""}`}
              disabled={generating}
              title={`${sc.itemName} · ${sc.itemCategory}`}>
              <div className="scenario-chip-label">{sc.chip}</div>
              <div className="scenario-chip-sub">{sc.sub}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="workbench" style={{ marginTop: 24 }}>
        {/* ── INPUT PANEL ── */}
        <div className="panel panel-sticky">
          <div className="panel-title">
            <h3>{t.inputPanelTitle || "Input"}</h3>
            <span className="step">01 / 02</span>
          </div>

          <div className="form-group">
            <label className="label" htmlFor="reviewer-tabs">{t.reviewerLabel || "Reviewer"}</label>
            <div className="tabs" id="reviewer-tabs" role="tablist">
              {[["user", t.userIdTab || "User ID"], ["persona", t.personaTab || "Describe persona"]].map(([mode, lbl]) => (
                <div key={mode} role="tab" className={`tab ${inputMode === mode ? "active" : ""}`}
                     onClick={() => setInputMode(mode)} aria-selected={inputMode === mode}>{lbl}</div>
              ))}
            </div>
            {inputMode === "user" ? (
              <input id="user-id-input" className="input mono" value={userId}
                     onChange={e => setUserId(e.target.value)} placeholder={t.userIdPlaceholder || "e.g. ChiomaNwankwo92"} />
            ) : (
              <textarea id="persona-input" className="textarea" value={persona}
                        onChange={e => setPersona(e.target.value)}
                        placeholder={t.personaPlaceholder || 'e.g. "A picky Lagos foodie who loves amala"'} />
            )}
          </div>

          <div className="divider"></div>

          <div className="form-group">
            <label className="label" htmlFor="item-name">{t.itemNameLabel || "Item · Name"}</label>
            <input id="item-name" className="input" value={itemName} onChange={e => setItemName(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="label" htmlFor="item-cat">{t.itemCategoryLabel || "Item · Category"}</label>
            <input id="item-cat" className="input" value={itemCategory} onChange={e => setItemCategory(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="label" htmlFor="item-desc">{t.itemDescLabel || "Item · Description"}</label>
            <textarea id="item-desc" className="textarea" value={itemDesc} onChange={e => setItemDesc(e.target.value)} />
          </div>

          <div className="divider"></div>

          <div className="vibe-row">
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{t.vibeModeLabel || "Naija Vibe Mode"}</div>
              <div className="dim" style={{ fontSize: 12 }}>
                {vibe ? (t.vibeModeOn || "Pidgin-heavy register active") : (t.vibeModeOff || "Standard English register")}
              </div>
            </div>
            <NaijaVibeToggle vibe={vibe} setVibe={setVibe} label="" />
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}
                  onClick={generate} disabled={generating || !itemName} aria-busy={generating}>
            {generating ? <span className="mono cursor">{t.generating || "The agent dey think..."}</span>
              : <>{t.generateBtn || "Generate Review"} <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></>}
          </button>

          {error && <ErrorBanner message={error} label={t.errorLabel || "Generation failed"} onRetry={generate} />}
        </div>

        {/* ── OUTPUT PANEL ── */}
        <div className="col" style={{ gap: 20 }} ref={outputRef}>
          {/* Review card */}
          <div className={`review-card ${vibe ? "amber" : ""}`} aria-live="polite">
            <div className="between" style={{ marginBottom: 16 }}>
              <div className="eyebrow" style={{ color: vibe ? "var(--amber)" : "var(--teal)" }}>
                {vibe ? (t.vibeLabel || "★ Naija Vibe Output") : (t.generatedLabel || "Generated Review")}
              </div>
              <div className="row" style={{ gap: 8 }}>
                {result && <CopyButton text={result.review_text} />}
                <span className="mono dim" style={{ fontSize: 11 }}>{itemName ? itemName.slice(0, 24).toUpperCase() : "—"}</span>
              </div>
            </div>

            {result ? (
              <>
                <p className="review-text">{typed}
                  {typed.length < result.review_text.length && <span className="cursor" aria-hidden="true"></span>}
                </p>
                <div className="review-meta">
                  <div className="col" style={{ gap: 6 }}>
                    <div className="mono dim" style={{ fontSize: 10, letterSpacing: "0.14em" }}>{t.ratingLabel || "RATING"}</div>
                    <div className="row" style={{ gap: 8 }}>
                      <Stars value={result.rating} size={17}/>
                      <span className="mono" style={{ fontSize: 14, color: "var(--amber)" }}>{result.rating.toFixed(1)}</span>
                    </div>
                  </div>
                  <div style={{ flex: 1 }}></div>
                  <ConfidenceChip value={result.confidence} label="Conf"/>
                  {vibe && result.vibe_score != null && (
                    <span className="chip med" title="Abeg Score — cultural authenticity">
                      <span className="chip-dot"></span>Vibe <span className="mono">{result.vibe_score.toFixed(2)}</span>
                    </span>
                  )}
                </div>
              </>
            ) : generating ? (
              <div className="review-skeleton">
                <SkeletonLine width="95%" height={13} style={{ marginBottom: 9 }}/>
                <SkeletonLine width="88%" height={13} style={{ marginBottom: 9 }}/>
                <SkeletonLine width="76%" height={13} style={{ marginBottom: 9 }}/>
                <SkeletonLine width="60%" height={13}/>
                <div className="mono cursor dim" style={{ fontSize: 13, marginTop: 12 }}>{t.checkingMsg || "Checking the vibe..."}</div>
              </div>
            ) : (
              <div className="review-empty">
                <div style={{ textAlign: "center" }}>
                  <div className="mono dim" style={{ fontSize: 12, letterSpacing: "0.14em", marginBottom: 8 }}>READY</div>
                  <div style={{ fontSize: 14, color: "var(--fg-faint)" }}>
                    {activeScenario ? "Press Generate ↑ to run the selected scenario" : (t.emptyMsg || "Select a scenario above or fill the form, then press Generate.")}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Meta cards */}
          {result && (
            <div className="grid-2" style={{ gap: 14 }}>
              <div className="card" style={{ padding: 16 }}>
                <div className="eyebrow" style={{ marginBottom: 8 }}>{t.fingerprintMatchLabel || "Fingerprint Match"}</div>
                <div style={{ fontSize: 14, color: "var(--fg)", lineHeight: 1.5 }}>{result.fingerprint_match}</div>
              </div>
              <div className="card" style={{ padding: 16 }}>
                <div className="eyebrow" style={{ marginBottom: 8 }}>{t.styleNotesLabel || "Style Notes"}</div>
                <div style={{ fontSize: 14, color: "var(--fg)", lineHeight: 1.5 }}>{result.style_notes}</div>
              </div>
            </div>
          )}

          {/* Radar */}
          <div className="card" style={{ padding: 24 }}>
            <div className="between" style={{ marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 18 }}>{t.fingerprintTitle || "Behavioural Fingerprint"}</h3>
                <div className="dim" style={{ fontSize: 13, marginTop: 4 }}>{t.fingerprintSub || "7 dimensions · Hover any axis to inspect"}</div>
              </div>
              <span className="chip lav"><span className="chip-dot"></span>
                {inputMode === "user" ? userId : (SCENARIOS.find(s => s.id === activeScenario)?.chip || "Custom persona")}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "center", paddingTop: 8 }}>
              <RadarChart data={radarData} size={360} color={vibe ? "var(--amber)" : "var(--teal)"} />
            </div>
          </div>

          {/* Reasoning trace — animated */}
          <div className="card collapse" data-open={traceOpen}>
            <button className="collapse-head" onClick={() => setTraceOpen(o => !o)}
                    aria-expanded={traceOpen} aria-controls="trace-body">
              <div>
                <h3 style={{ fontSize: 18 }}>{t.reasoningTitle || "Reasoning Trace"}</h3>
                <div className="dim" style={{ fontSize: 13, marginTop: 4 }}>
                  {reasoningSteps.length > 0 ? reasoningSteps.length : (SCENARIOS.find(s => s.id === activeScenario)?.reasoning.length || 6)}{" "}
                  {t.reasoningSub || "steps · LangGraph state machine"}
                </div>
              </div>
              <svg className="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
            {traceOpen && (
              <div id="trace-body" className="trace" style={{ marginTop: 12 }}>
                {(reasoningSteps.length > 0 ? reasoningSteps : (SCENARIOS.find(s => s.id === activeScenario)?.reasoning || [])).map((s, i) => (
                  <div key={i} className={`trace-step ${(result ? i < visibleSteps : true) ? "done" : ""}`}
                       style={{ opacity: result ? (i < visibleSteps ? 1 : 0.15) : 0.4, transition: "opacity 0.3s ease" }}>
                    <div className="trace-num" aria-hidden="true">{String(s.step || i + 1).padStart(2, "0")}</div>
                    <div className="trace-body">
                      <div className="trace-title">{s.title}</div>
                      <div className="trace-detail">{s.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { TaskA });
