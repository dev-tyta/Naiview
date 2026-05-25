/* TASK A — Review Generation Interface */

const { useState, useEffect, useCallback, useRef } = React;

/* ================================================================
   Demo scenarios — 4 cities, 4 categories, distinct fingerprints
================================================================ */
const SCENARIOS = [
  {
    id: "lekki-amala", chip: "Lekki Amala", sub: "Mama Chi's · Buka",
    inputMode: "persona",
    persona: "A trendy Lekki resident who enjoys authentic street food but expects high standards. Values the 'soul' of a buka over posh decor. Heavy Pidgin user.",
    userId: "Tayo_Lekki_Vibe",
    itemName: "Mama Chi's Buka",
    itemCategory: "Buka / Mama Put · Lekki",
    itemDesc: "Famous amala spot in Lekki. Known for cotton-soft amala, ewedu, and gbegiri. Popular with both locals and office workers.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.85 },
      { key: "verbosity",  label: "Verbosity",           value: 0.62 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.92 },
      { key: "topic",      label: "Topic Focus",         value: 0.78 },
      { key: "consistency",label: "Consistency",         value: 0.84 },
      { key: "recency",    label: "Recency Weight",       value: 0.71 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.95 },
    ],
    reviewVibe: `Ah, Mama Chi's Buka for Lekki don scatter my head! I been dey hear about am for long, say their amala dey burst brain, but I no believe until I enter myself. Omo, the amala soft like cotton, and the ewedu and gbegiri? Chai! E reach bone. The meat wey dem put inside, big and juicy. And the price? E get value for money, I swear. Even though the place dey small and sometimes e dey hot small, the food make up for everything. This place don sweet me die. Na here I go always patronize whenever I dey Lekki side.`,
    reviewEn: `Mama Chi's Buka in Lekki exceeded my expectations. I had heard much about their amala, but experiencing it firsthand was different. The amala is exceptionally soft, and the ewedu and gbegiri are flavorful. The portions of meat are generous and juicy. It offers great value for money. Although the space is small and can be warm, the quality of the food justifies it. I will certainly be a regular patron whenever I am in the Lekki area.`,
    rating: 5.0, confidence: 0.94, vibeScore: 0.92,
    fingerprintMatch: "Very High — identified as heavy Pidgin user with high emotional intensity for food quality",
    styleNotes: "Enthusiastic, Pidgin-heavy. Focuses on texture ('soft like cotton') and emotional response ('scatter my head').",
    reasoning: [
      { step: 1, title: "User identified: Lekki street-food enthusiast", detail: "Heavy Pidgin marker detected · High-affinity for Buka category" },
      { step: 2, title: "Category match: 98%", detail: "Buka / Mama Put — exact match for user's primary historical domain" },
      { step: 3, title: "Region detected: Lagos (Lekki)", detail: "Lekki, Okada, Gbegiri signals · region confidence 0.96" },
      { step: 4, title: "Sentiment predicted: Highly Positive", detail: "Persona's 'cotton-soft' amala preference matched with item metadata" },
      { step: 5, title: "Pidgin register: Amplified", detail: "Naija slang index 0.95 · Heavy use of 'Omo', 'Chai', 'Scatter' markers" },
      { step: 6, title: "Vibe Check: 0.92 ✓", detail: "cultural_authenticity 0.94 · cultural_accuracy 0.91 · persona_consistency 0.89" },
    ],
  },
  {
    id: "abuja-buka", chip: "Abuja Lunch", sub: "Iya Basira · Wuse 2",
    inputMode: "persona",
    persona: "A Wuse 2 professional who values speed and quality. Writes balanced reviews in standard English with mild Nigerian emphasis markers.",
    userId: "Wuse2_Pro",
    itemName: "Iya Basira's Buka",
    itemCategory: "Buka / Mama Put · Wuse 2",
    itemDesc: "Prompt service amala spot in the heart of Wuse 2, Abuja. Known for smooth amala and generous portions.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.75 },
      { key: "verbosity",  label: "Verbosity",           value: 0.55 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.68 },
      { key: "topic",      label: "Topic Focus",         value: 0.82 },
      { key: "consistency",label: "Consistency",         value: 0.94 },
      { key: "recency",    label: "Recency Weight",       value: 0.76 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.42 },
    ],
    reviewVibe: `I recently visited Iya Basira's Buka in Wuse 2, and I must say, I was pleasantly surprised. The amala and ewedu were particularly good; the ewedu had just the right amount of thickness and the amala was smooth, no lumps at all. The portions are quite generous, and the prices are very reasonable, especially considering the location. The service was prompt and the staff were friendly. But the food was really nice o, I will definitely return.`,
    reviewEn: `I was pleasantly surprised by Iya Basira's Buka in Wuse 2. The amala was smooth and the ewedu had the perfect consistency. Portions are generous and pricing is very fair for a Wuse 2 location. Service was prompt and professional. A reliable choice for lunch.`,
    rating: 4.0, confidence: 0.88, vibeScore: 0.74,
    fingerprintMatch: "High — matches FCT professional persona with preference for prompt service",
    styleNotes: "Balanced, articulate. Uses 'really nice o' as a natural cultural closer.",
    reasoning: [
      { step: 1, title: "User identified: Abuja professional", detail: "Wuse 2, FCT signals · Preference for efficiency and balanced tone" },
      { step: 2, title: "Category match: 91%", detail: "Buka / Mama Put — consistent with user's lunchtime review history" },
      { step: 3, title: "Region detected: Abuja", detail: "Wuse 2, FCT markers · region confidence 0.89" },
      { step: 4, title: "Sentiment predicted: Positive 4.0", detail: "Efficiency + location value alignment → positive rating" },
      { step: 5, title: "Register: Natural English/Pidgin mix", detail: "Naija slang index 0.42 · Standard English with Nigerian focus markers" },
      { step: 6, title: "Vibe Check: 0.74 ✓", detail: "cultural_authenticity 0.72 · cultural_accuracy 0.76 · persona_consistency 0.75" },
    ],
  },
  {
    id: "kano-tuwo", chip: "Kano Gem", sub: "Mama Aisha · Sabon Gari",
    inputMode: "persona",
    persona: "A Kano local who values Northern authenticity. Uses Hausa loanwords naturally in English sentences.",
    userId: "Kano_Heritage",
    itemName: "Mama Aisha's Buka",
    itemCategory: "Buka / Mama Put · Sabon Gari",
    itemDesc: "Traditional Northern spot near Sabon Gari market, Kano. Famous for Tuwo Shinkafa and Miyan Kuka.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.82 },
      { key: "verbosity",  label: "Verbosity",           value: 0.48 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.72 },
      { key: "topic",      label: "Topic Focus",         value: 0.88 },
      { key: "consistency",label: "Consistency",         value: 0.91 },
      { key: "recency",    label: "Recency Weight",       value: 0.64 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.58 },
    ],
    reviewVibe: `Mama Aisha's Buka near Sabon Gari market is a proper gem. I stopped by for lunch after a long morning of errands, and the food was really nice o. I had the Tuwo Shinkafa with Miyan Kuka, and it tasted just like my grandmother used to make. The portions are generous, and the prices are very reasonable – especially considering how close it is to the market. The service was quick and friendly. I will definitely return when I'm craving a taste of home. Ranka dede to Mama Aisha!`,
    reviewEn: `Mama Aisha's Buka in Sabon Gari is an authentic gem. The Tuwo Shinkafa and Miyan Kuka are traditionally prepared and reminiscent of home cooking. Portions are generous and pricing is excellent for the market area. Service is quick and welcoming. Highly recommended for authentic Northern cuisine.`,
    rating: 4.0, confidence: 0.91, vibeScore: 0.86,
    fingerprintMatch: "High — Northern identity confirmed via Hausa loanwords and regional food focus",
    styleNotes: "Respectful, nostalgic. Uses 'Ranka dede' as a regional honorific.",
    reasoning: [
      { step: 1, title: "User identified: Northern traditionalist", detail: "Sabon Gari, Kano signals · Northern food vocabulary" },
      { step: 2, title: "Category match: 95%", detail: "Traditional Northern cuisine — matches user's cultural affinity" },
      { step: 3, title: "Region detected: Kano", detail: "Sabon Gari, Hausa loanwords · region confidence 0.94" },
      { step: 4, title: "NLM: Hausa loanword injection", detail: "Mapped 'Respect' to 'Ranka dede' based on regional marker match" },
      { step: 5, title: "Register: Northern Nigerian English", detail: "Naija slang index 0.58 · Dialect-specific emphasis markers" },
      { step: 6, title: "Vibe Check: 0.86 ✓", detail: "cultural_authenticity 0.88 · cultural_accuracy 0.85 · persona_consistency 0.84" },
    ],
  },
  {
    id: "surulere-salon", chip: "Surulere Salon", sub: "Hair Today · Beauty",
    inputMode: "persona",
    persona: "A Surulere resident who values professional service and cleanliness in beauty salons. Direct and observant.",
    userId: "Surulere_Style",
    itemName: "Hair Today, Gone Tomorrow",
    itemCategory: "Beauty / Salon · Surulere",
    itemDesc: "Well-maintained salon in Surulere. Specializes in trims, deep conditioning, and professional styling.",
    fingerprint: [
      { key: "generosity", label: "Generosity",         value: 0.68 },
      { key: "verbosity",  label: "Verbosity",           value: 0.72 },
      { key: "emotion",    label: "Emotional Intensity", value: 0.61 },
      { key: "topic",      label: "Topic Focus",         value: 0.75 },
      { key: "consistency",label: "Consistency",         value: 0.86 },
      { key: "recency",    label: "Recency Weight",       value: 0.59 },
      { key: "naija",      label: "Naija Slang Index",   value: 0.35 },
    ],
    reviewVibe: `I recently visited 'Hair Today, Gone Tomorrow' in Surulere, and I must say, I was quite impressed. Finding a good salon in Lagos can be a real struggle, but this one is definitely a keeper. I went in for a simple trim and a deep conditioning treatment. The stylist, Tolu, was very professional and listened carefully to what I wanted. She didn't just chop off my hair like some other places I've been to. The salon itself is clean and well-maintained. I will definitely be returning. The traffic getting there was a bit mad, but it was worth it o!`,
    reviewEn: `I was impressed by 'Hair Today, Gone Tomorrow' in Surulere. The service was professional and the stylist listened to my requirements perfectly. The facility is clean and well-maintained. Despite the traffic in the area, the quality of the service makes it a worthwhile destination.`,
    rating: 5.0, confidence: 0.86, vibeScore: 0.71,
    fingerprintMatch: "Moderate-High — matches service-conscious Surulere persona",
    styleNotes: "Observant, appreciative. Mentions staff by name (Tolu) and local context (traffic).",
    reasoning: [
      { step: 1, title: "User identified: Surulere local", detail: "Surulere, Lagos traffic signals · 8 service-domain reviews" },
      { step: 2, title: "Category match: 88%", detail: "Beauty / Salon — matches persona's demonstrated interest area" },
      { step: 3, title: "Region detected: Lagos", detail: "Surulere, Lagos traffic markers · region confidence 0.87" },
      { step: 4, title: "Sentiment predicted: Positive 5.0", detail: "Cleanliness + professionalism scores above user's threshold" },
      { step: 5, title: "Register: Natural English", detail: "Naija slang index 0.35 · Minimal Pidgin, high lexical clarity" },
      { step: 6, title: "Vibe Check: 0.71 ✓", detail: "cultural_authenticity 0.70 · cultural_accuracy 0.73 · persona_consistency 0.71" },
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
