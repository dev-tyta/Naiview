/* EVALUATION — Metrics dashboard + Side-by-side comparison */

const { useState } = React;

const METRICS = [
  { key: "rouge",  label: "ROUGE-L",         value: 0.42, baseline: 0.31, hint: "Lexical overlap with human reference reviews" },
  { key: "bert",   label: "BERTScore",        value: 0.78, baseline: 0.69, hint: "Semantic similarity to human-written output" },
  { key: "rmse",   label: "Rating RMSE",      value: 0.61, baseline: 0.89, hint: "Star prediction error — lower is better", invert: true },
  { key: "ndcg",   label: "NDCG@10",          value: 0.74, baseline: 0.58, hint: "Ranking quality at top-10 recommendations" },
  { key: "vibe",   label: "Naija Vibe Score", value: 0.81, baseline: 0.32, hint: "Cultural authenticity — avg Abeg score across test set" },
  { key: "human",  label: "Human Eval",       value: 0.87, baseline: 0.71, hint: "Preference rate · pilot cohort · 12 native speakers" },
];

const COMPARISONS = [
  {
    input: { user: "AdekunleRoads", item: "Kilimanjaro Restaurant, Wuse II, Abuja" },
    generic: "The restaurant offers a pleasant dining experience with a diverse menu. The service is attentive and the ambiance is nice. I would recommend it for a casual dinner. Rating: 4/5",
    naija: "Guy, Kilimanjaro no dey disappoint. The suya platter was fire — proper Abuja standard. Waiter dem sabi their work, no wahala. The only thing be say parking for Wuse II na war, but once you enter, e worth am. If you dey Abuja and you never go here, you dey owe yourself. 4 stars — would be 5 but make dem reduce that pepper small for the coleslaw 😂",
    rating: 4,
  },
  {
    input: { user: "ChiomaNwankwo92", item: "Mama Cass Restaurant, Victoria Island, Lagos" },
    generic: "Had a pleasant meal at Mama Cass Restaurant on Victoria Island. The jollof rice was flavorful and well-prepared, though service could have been faster. Pricing was reasonable for the area. I would consider returning.",
    naija: "Abeg, if you never chop for Mama Cass, you never start. The jollof rice hit different — proper party jollof vibes. Service was a bit slow sha, but the food make up for am. For VI price, e dey reasonable. I go come back with my squad next weekend. 4 stars because that AC need to work harder!",
    rating: 4,
  },
  {
    input: { user: "TundeGames", item: "Itel S25 Smartphone" },
    generic: "The Itel S25 is a budget-friendly smartphone offering decent performance for everyday use. The camera quality is acceptable, the battery life is sufficient. A reasonable choice for users on a tight budget.",
    naija: "For this price wey them dey sell am, the Itel S25 dey try sha. Battery na the main thing — e fit reach two days if you no dey play game too much. Camera no be the best but for WhatsApp picture, e do well. If you no get money for iPhone, this one fit hold body.",
    rating: 3,
  },
  {
    input: { user: "FunkeAdebayo", item: "Things Fall Apart by Chinua Achebe (Reread)" },
    generic: "A profound classic that captures pre-colonial Igbo society with remarkable depth. The prose is accessible and the themes remain relevant. Highly recommended for readers interested in African literature.",
    naija: "I read this book again, and it still hit me like the first time. Achebe no dey play — every chapter wey you read, you go feel say na your grandfather dey talk. For Naija reader, this book pass book, e be like family history. If you never read am, abeg start today.",
    rating: 5,
  },
  {
    input: { user: "EmekaLagosBoy", item: "Sundowner at The Wheatbaker, Ikoyi" },
    generic: "An elegant venue with a sophisticated atmosphere. The cocktail selection is curated and the views are pleasant. Service is attentive. Suitable for a refined evening out.",
    naija: "Wheatbaker rooftop na proper Lagos energy. Sun dey set, drinks dey cold, mix dey play — wetin person fit ask for again? Price no be small thing but you dey pay for the vibe, no be the alcohol. If you wan impress person, e dey work. Just no come with empty pocket abeg.",
    rating: 5,
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
  const c = COMPARISONS[idx];

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
        <div className="eyebrow" style={{ marginBottom: 16 }}>{t.quantLabel || 'Quantitative Results'}</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {METRICS.map(m => (
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
