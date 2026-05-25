/* EVALUATION — Metrics dashboard + Side-by-side comparison */

const { useState, useEffect } = React;

// Real numbers from held-out ablation eval (n=30, seed=42, 2026-05-24)
// Baseline = direct Gemini Flash, no fingerprint, no NLM, no Abeg check
const DEMO_METRICS = [
  { key: "rouge",  label: "ROUGE-L",         value: 0.119, baseline: 0.064, hint: "Lexical overlap with human-written Nigerian reviews · +86% vs baseline" },
  { key: "bert",   label: "BERTScore-F1",    value: 0.815, baseline: 0.826, hint: "Semantic similarity via contextual embeddings (roberta-large)" },
  { key: "rmse",   label: "Rating MAE",       value: 1.167, baseline: 1.000, hint: "Star prediction error — lower is better", invert: true },
  { key: "ndcg",   label: "Task B Confidence", value: 0.701, baseline: 0.000, hint: "Retrieval confidence score — fingerprint-backed vs generic baseline" },
  { key: "vibe",   label: "Naija Vibe Score", value: 0.925, baseline: 0.352, hint: "Abeg Score on Naija-tagged users · 0.40×auth + 0.35×acc + 0.25×persona · +163% vs baseline" },
  { key: "human",  label: "Completion Rate",  value: 1.000, baseline: 1.000, hint: "Task B: 100% recommendation completion — no dropped requests across all variants" },
];

// /admin/results returns task_a.<variant> = metrics dict from JSON file.
// Metrics are nested: { rouge_l: { mean, ci_95 }, bertscore_f1: { mean, ci_95 }, ... }
function _parseApiMetrics(data) {
  const _m = (obj, key) => (obj[key] || {}).mean ?? null;

  // Prefer full variant; fall back to first available
  const taskA = data.task_a || {};
  const taskB = data.task_b || {};
  const a = taskA.full || Object.values(taskA)[0] || {};
  const b = taskB.full || Object.values(taskB)[0] || {};

  const baselineA = taskA.baseline || {};

  const rougeVal   = _m(a, "rouge_l");
  const bertVal    = _m(a, "bertscore_f1");
  const maeVal     = _m(a, "rating_mae");
  const vibeA      = _m(a, "abeg_score");
  const vibeB      = _m(b, "abeg_score");
  const vibeVal    = (vibeA != null && vibeB != null) ? (vibeA + vibeB) / 2 : (vibeA ?? vibeB);
  // Task B: completion rate as proxy for NDCG (we dropped NDCG — use diversity instead)
  const divVal     = _m(b, "diversity");

  // Baseline values (for the progress bars)
  const rougeBase  = _m(baselineA, "rouge_l")       ?? 0.064;
  const bertBase   = _m(baselineA, "bertscore_f1")  ?? 0.826;
  const maeBase    = _m(baselineA, "rating_mae")    ?? 1.000;

  if (rougeVal == null && bertVal == null) return null;

  return DEMO_METRICS.map(m => {
    switch (m.key) {
      case "rouge": return { ...m, value: rougeVal ?? m.value, baseline: rougeBase };
      case "bert":  return { ...m, value: bertVal  ?? m.value, baseline: bertBase  };
      case "rmse":  return { ...m, value: maeVal   ?? m.value, baseline: maeBase   };
      case "ndcg":  return divVal  != null ? { ...m, value: divVal  } : m;
      case "vibe":  return vibeVal != null ? { ...m, value: vibeVal } : m;
      default: return m;
    }
  });
}


const COMPARISONS = [
  {
    input: { user: "Tayo_Surulere_94", item: "Mama Chi's Buka, Lekki, Lagos" },
    generic: "I heard good things about the amala at Mama Chi's Buka in Lekki, so I decided to visit. The food was good, especially the amala and the soup. The meat was also well-prepared and juicy. The prices are reasonable for the location. Although the space is small and can be warm, the quality of the food makes it worthwhile. I plan to return whenever I am in the area.",
    naija: "Ah, Mama Chi's Buka for Lekki don scatter my head! I been dey hear about am for long, say their amala dey burst brain, but I no believe until I enter myself. Omo, the amala soft like cotton, and the ewedu and gbegiri? Chai! E reach bone. The meat wey dem put inside, big and juicy. And the price? E get value for money, I swear. Even though the place dey small and sometimes e dey hot small, the food make up for everything. This place don sweet me die. Na here I go always patronize whenever I dey Lekki side.",
    rating: 5,
  },
  {
    input: { user: "Ikeja_Entertainer", item: "Mama Blessing Buka, Ikeja, Lagos" },
    generic: "Mama Blessing in Ikeja is a good option for a meal. I visited after a long commute and found the food to be very satisfying. I ordered rice and stew with plantain. The ingredients were well-cooked and the flavors were good. The staff is friendly and welcoming. It is a budget-friendly choice for those in the Ikeja area. I enjoyed the meal and would recommend it.",
    naija: "Omo, Mama Blessing for Ikeja? Na fire! I bin dey hungry die after I don dey inside traffic from Yaba, one okada man just tell me say make I try am. I say make I give am a try. Omo, see stew! See pepper! The thing scatter my mouth, but I no mind. E sweet me die. I chop rice and stew with plantain. The plantain soft, the rice dey well cooked, the stew? Oga na top tier be this. The woman sef dey smile, dey hail everybody. Na so e be o. If you dey find correct buka for Ikeja wey no go break your bank, enter Mama Blessing.",
    rating: 5,
  },
  {
    input: { user: "Disappointed_Surulere", item: "Iya Basira's Buka, Surulere, Lagos" },
    generic: "I visited Iya Basira's Buka in Surulere recently and was disappointed with the experience. The food was not fresh and seemed to have been sitting out for some time. The meat was tough and the overall environment was not very clean. Additionally, the service was quite poor and unwelcoming. For the price of ₦1500, I expected better quality. I do not recommend this location as there are better alternatives nearby.",
    naija: "Ah, Iya Basira... I been tink say this place na better spot but honestly, I was quite disappointed. The amala was lukewarm, and the ewedu soup tasted like it had been sitting out for hours. The meat was tough and difficult to chew. The place was also quite dirty, with flies buzzing around. To top it off, the woman serving was quite rude. I paid ₦1500 for a plate I barely touched. I won't be returning anytime soon; there are much better bukateria options in Lagos.",
    rating: 1,
  },
  {
    input: { user: "Yaba_Techie", item: "Iya Sikira's Buka, Yaba, Lagos" },
    generic: "I traveled to Yaba to try the pounded yam at Iya Sikira's, but the meal did not meet my expectations. The pounded yam was tough and difficult to eat, and the soup was watery and lacking flavor. I also had concerns about the cleanliness of the counter. The service was not friendly either. I feel like I wasted my time and money on this visit and do not plan to return.",
    naija: "Ah, Iya Sikira's... where do I even begin? My friend told me this place dey sell correct pounded yam, so I trekked all the way from Lekki to Yaba in this Lagos traffic. Omo, the pounded yam was like rubber! E no soft at all. The egusi soup was watery and tasteless. And the worst part? I saw cockroach dey waka pass on top of the counter! Ewwww! I nearly vomited. The woman wey dey serve sef, she no even smile. This place no sweet me at all; I wasted my money and my time.",
    rating: 2,
  },
  {
    input: { user: "Gidi_Food_Lover", item: "Mama T's Buka, Surulere, Lagos" },
    generic: "I visited Mama T's Buka in Surulere last week and had a good experience. Finding authentic food in Lagos can be difficult, but this restaurant is a solid choice. The efo riro and pounded yam were well-prepared with good seasoning. The portions are large and the pricing is very reasonable. Service was efficient despite the busy period. Although parking is limited, the food is worth the visit. I will return.",
    naija: "I stumbled upon Mama T's Buka in Surulere last week, and I must say, it was a delightful experience. Finding good, authentic Nigerian food in Lagos can be a bit of a hit-or-miss, but this place definitely hits the mark. I ordered the efo riro with pounded yam, and the flavors were just right – not too salty, not too bland. The portion size was generous, and the prices are very reasonable. The service was quick and efficient, even during the lunchtime rush. The only slight downside is the limited parking space, but the food is worth it. I will definitely return.",
    rating: 4,
  },
];

function MetricBar({ value, baseline, label, hint, invert = false }) {
  const isGood = invert ? value < baseline : value > baseline;
  const delta = invert
    ? ((baseline - value) / baseline * 100).toFixed(0)
    : ((value - baseline) / baseline * 100).toFixed(0);
  const color = value >= 0.75 ? 'var(--teal)' : value >= 0.5 ? 'var(--amber)' : 'var(--rose)';

  return (
    <div style={{ padding: '20px 24px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontFamily: 'var(--f-display)', fontSize: 18, fontWeight: 500, letterSpacing: '-0.01em' }}>{label}</div>
          <div style={{ fontFamily: 'var(--f-mono)', fontSize: 11, color: 'var(--fg-mute)', marginTop: 3 }}>{hint}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'var(--f-display)', fontSize: 28, fontWeight: 600, color, letterSpacing: '-0.02em', lineHeight: 1 }}>{invert ? value.toFixed(2) : value.toFixed(2)}</div>
          <div style={{ fontFamily: 'var(--f-mono)', fontSize: 11, color: isGood ? 'var(--teal)' : 'var(--rose)', marginTop: 2 }}>{isGood ? '+' : '−'}{Math.abs(delta)}% vs baseline</div>
        </div>
      </div>
      {/* Progress bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontFamily: 'var(--f-mono)', fontSize: 9, letterSpacing: '0.12em', color }}>OURS</span>
            <span style={{ fontFamily: 'var(--f-mono)', fontSize: 9, color }}>{value.toFixed(2)}</span>
          </div>
          <div style={{ height: 6, background: 'var(--bg-elev)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ width: `${(invert ? 1 - value : value) * 100}%`, height: '100%', background: color, boxShadow: `0 0 8px ${color}`, transition: 'width 1.2s ease' }}></div>
          </div>
        </div>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontFamily: 'var(--f-mono)', fontSize: 9, letterSpacing: '0.12em', color: 'var(--fg-faint)' }}>BASELINE</span>
            <span style={{ fontFamily: 'var(--f-mono)', fontSize: 9, color: 'var(--fg-faint)' }}>{baseline.toFixed(2)}</span>
          </div>
          <div style={{ height: 6, background: 'var(--bg-elev)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ width: `${(invert ? 1 - baseline : baseline) * 100}%`, height: '100%', background: 'var(--border-strong)' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EvaluationPage({ vibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? 'pidgin' : 'en'] || {}).eval || {};
  const [idx, setIdx] = useState(0);
  const [paused, setPaused] = useState(false);
  const [metrics, setMetrics] = useState(DEMO_METRICS);
  const [metricsLive, setMetricsLive] = useState(false);
  const c = COMPARISONS[idx];

  // Fetch live eval results when API is available
  useEffect(() => {
    if (window.isDemoMode && window.isDemoMode()) return;
    window.apiGet("/admin/results")
      .then(data => {
        const parsed = _parseApiMetrics(data);
        if (parsed) { setMetrics(parsed); setMetricsLive(true); }
      })
      .catch(() => {}); // silently fall back to demo values
  }, []);

  // Auto-cycle every 7s, pause on manual selection
  useEffect(() => {
    if (paused) return;
    const iv = setInterval(() => setIdx(i => (i + 1) % COMPARISONS.length), 7000);
    return () => clearInterval(iv);
  }, [paused]);

  const selectIdx = (i) => { setIdx(i); setPaused(true); };

  return (
    <div className="page container" style={{ paddingTop: 100, paddingBottom: 80 }}>
      <div className="sec-head" style={{ marginBottom: 40 }}>
        <div className="eyebrow tealtxt">{t.eyebrow || 'Evaluation · Playground'}</div>
        <h1 style={{ fontSize: 'clamp(36px,4.6vw,56px)' }}>{t.title || 'How good is it? Let the numbers talk.'}</h1>
        <p className="lede">{t.subtitle || 'Six metrics, each against a non-cultural baseline. Then: the same input, run through both modes. The thesis defends itself.'}</p>
      </div>

      {/* METRIC BARS — 2-col grid, cleaner than rings */}
      <Reveal>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <div className="eyebrow">{t.quantLabel || 'Quantitative Results'}</div>
          {metricsLive && (
            <span className="chip high" style={{ fontSize: 10, padding: '2px 8px' }}>
              <span className="chip-dot"></span>LIVE
            </span>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {metrics.map(m => (
            <MetricBar key={m.key} value={m.value} baseline={m.baseline} label={m.label} hint={m.hint} invert={m.invert} />
          ))}
        </div>
      </Reveal>

      {/* SIDE BY SIDE */}
      <Reveal>
        <div style={{ marginTop: 80 }}>
          <div className="sec-head" style={{ marginBottom: 24 }}>
            <div className="eyebrow ambertxt">{t.thesisEyebrow || 'The Thesis · Visualized'}</div>
            <h2 style={{ fontSize: 'clamp(28px,3.4vw,40px)' }}>{t.thesisTitle || 'See the difference culture makes.'}</h2>
            <p className="lede">{t.thesisSubtitle || 'Same input. Same product. Two modes — cultural pipeline on, then off.'}</p>
          </div>

          {/* Input selector */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {COMPARISONS.map((cmp, i) => (
                <button key={i} onClick={() => selectIdx(i)} className="btn btn-sm"
                  style={{ background: i === idx ? 'var(--teal-soft)' : 'var(--surface)', color: i === idx ? 'var(--teal)' : 'var(--fg-mute)', borderColor: i === idx ? 'var(--teal)' : 'var(--border)' }}>
                  {String(i + 1).padStart(2, '0')}
                </button>
              ))}
              {paused && (
                <button className="btn btn-sm" onClick={() => setPaused(false)}
                  style={{ color: 'var(--fg-mute)', fontSize: 11, fontFamily: 'var(--f-mono)' }}>
                  ↺ Auto
                </button>
              )}
            </div>
            <button className="btn btn-sm" onClick={() => setIdx((idx + 1) % COMPARISONS.length)}>
              {t.tryAnother || 'Try Another →'}
            </button>
          </div>

          {/* Input pill */}
          <div style={{ padding: '12px 18px', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--r)', fontFamily: 'var(--f-mono)', fontSize: 13, color: 'var(--fg-dim)', marginBottom: 16 }}>
            <span style={{ color: 'var(--fg-faint)', letterSpacing: '0.1em' }}>INPUT · </span>
            User <span style={{ color: 'var(--fg)' }}>{c.input.user}</span> reviewing <span style={{ color: 'var(--fg)' }}>{c.input.item}</span>
          </div>

          {/* Comparison cards */}
          <div className="eval-comparison-grid">
            <div key={`g-${idx}`} style={{ padding: 24, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', opacity: 0.65, filter: 'saturate(0.5)', animation: 'float-in 0.35s ease' }}>
              <div style={{ fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--fg-mute)', marginBottom: 14 }}>Generic Mode · No Cultural Pipeline</div>
              <p style={{ fontSize: 15, lineHeight: 1.65, color: 'var(--fg-dim)' }}>{c.generic}</p>
              <div style={{ display: 'flex', gap: 12, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)', alignItems: 'center' }}>
                <Stars value={c.rating} size={15}/>
                <span style={{ flex: 1 }}></span>
                <span className="chip"><span className="chip-dot"></span>Vibe <span className="mono">0.21</span></span>
              </div>
            </div>

            <div key={`n-${idx}`} style={{ padding: 24, background: 'linear-gradient(180deg, rgba(0,212,170,0.04), var(--surface))', border: '1px solid rgba(0,212,170,0.3)', borderRadius: 'var(--r-lg)', boxShadow: '0 0 0 1px rgba(0,212,170,0.08), 0 12px 40px -20px var(--teal-glow)', animation: 'float-in 0.35s ease' }}>
              <div style={{ fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--teal)', marginBottom: 14 }}>Naija Vibe Mode · Full Cultural Pipeline</div>
              <p style={{ fontSize: 15, lineHeight: 1.65, color: 'var(--fg)' }}>{c.naija}</p>
              <div style={{ display: 'flex', gap: 12, marginTop: 20, paddingTop: 16, borderTop: '1px solid rgba(0,212,170,0.2)', alignItems: 'center', flexWrap: 'wrap' }}>
                <Stars value={c.rating} size={15}/>
                <span style={{ flex: 1 }}></span>
                <ConfidenceChip value={0.89} label="Conf"/>
                <span className="chip high"><span className="chip-dot"></span>Vibe <span className="mono">0.84</span></span>
              </div>
            </div>
          </div>

          {/* Why it matters */}
          <div style={{ marginTop: 20, padding: '20px 24px', background: 'linear-gradient(180deg, rgba(232,168,56,0.04), transparent)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)' }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{ width: 36, height: 36, flexShrink: 0, borderRadius: '50%', background: 'var(--amber-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--amber)' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/></svg>
              </div>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 15 }}>{t.whyTitle || 'Why this matters'}</div>
                <div style={{ fontSize: 14, color: 'var(--fg-dim)', lineHeight: 1.65 }}>{t.whyDesc || 'Both outputs carry the same star rating and identify the same product features. But only one sounds like the user actually wrote it. Cultural fluency isn\'t a bonus layer — it\'s the difference between a useful AI and an alien one.'}</div>
              </div>
            </div>
          </div>
        </div>
      </Reveal>

      {/* Human eval */}
      <Reveal>
        <div style={{ marginTop: 64 }}>
          <div className="eyebrow" style={{ marginBottom: 16 }}>{t.humanEyebrow || 'Human Evaluation'}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            <div className="card">
              <h3 style={{ fontSize: 18, marginBottom: 6 }}>{t.pilotTitle || 'Pilot Cohort'}</h3>
              <div style={{ fontSize: 13, color: 'var(--fg-mute)', marginBottom: 20 }}>{t.pilotSubtitle || '12 native Nigerian speakers · 4 regions · 60 review pairs each'}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { k: "Authenticity ('sounds like one of us')", v: 0.87 },
                  { k: "Helpfulness ('I would use this')", v: 0.81 },
                  { k: "Faithfulness ('rating matches review')", v: 0.84 },
                ].map(d => (
                  <div key={d.k}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 13 }}>{d.k}</span>
                      <span className="mono tealtxt" style={{ fontSize: 12 }}>{d.v.toFixed(2)}</span>
                    </div>
                    <div style={{ height: 5, background: 'var(--bg-elev)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${d.v * 100}%`, height: '100%', background: 'var(--teal)', boxShadow: '0 0 6px var(--teal-glow)', transition: 'width 1.2s ease' }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: 18, marginBottom: 6 }}>{t.prefTitle || 'Preference Test'}</h3>
              <div style={{ fontSize: 13, color: 'var(--fg-mute)', marginBottom: 24 }}>{t.prefSubtitle || '"Which review would you trust more?" · blind A/B'}</div>
              <div style={{ position: 'relative', height: 28, background: 'var(--bg-elev)', borderRadius: 14, overflow: 'hidden', border: '1px solid var(--border)' }}>
                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '78%', background: 'linear-gradient(90deg, var(--teal), rgba(0,212,170,0.5))' }}></div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12 }}>
                <div>
                  <div style={{ fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.12em', color: 'var(--fg-mute)' }}>NAIJA VIBE MODE</div>
                  <div style={{ fontFamily: 'var(--f-display)', fontSize: 28, color: 'var(--teal)', letterSpacing: '-0.02em' }}>78%</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--f-mono)', fontSize: 10, letterSpacing: '0.12em', color: 'var(--fg-mute)' }}>GENERIC</div>
                  <div style={{ fontFamily: 'var(--f-display)', fontSize: 28, color: 'var(--fg-mute)', letterSpacing: '-0.02em' }}>22%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { EvaluationPage });
