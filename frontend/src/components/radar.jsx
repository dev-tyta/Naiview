/* Radar Chart — 7 behavioural fingerprint dimensions */

const { useEffect, useRef, useState } = React;

const RADAR_DESCRIPTIONS = {
  "Generosity":         "How generous this user is relative to platform average — high = consistently above-average stars",
  "Verbosity":          "How detailed their reviews are — high = long, thorough reviews; low = brief impressions",
  "Emotional Intensity":"How expressive the writing is — frequency of intensifiers and exclamation marks",
  "Topic Focus":        "How consistently they focus on the same topics — high = always mentions same things",
  "Consistency":        "Alignment between sentiment words and star rating — high = words match stars",
  "Recency Weight":     "How strongly recent reviews shape the fingerprint — high = very trend-sensitive",
  "Naija Slang Index":  "Fraction of tokens matching the Nigerian phrase library — cultural language density",
};

function RadarChart({
  data,
  size = 320,
  color = "var(--teal)",
  glow = true,
  animate = true,
}) {
  // data: [{ key, label, value (0-1) }, …]
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 60;
  const n = data.length;
  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;

  const [progress, setProgress] = useState(animate ? 0 : 1);
  const [hover, setHover] = useState(null);

  useEffect(() => {
    if (!animate) return;
    let raf;
    const start = performance.now();
    const tick = (t) => {
      const e = Math.min(1, (t - start) / 1100);
      // ease-out cubic
      setProgress(1 - Math.pow(1 - e, 3));
      if (e < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [animate, data]);

  const point = (i, v) => {
    const a = angle(i);
    const r = radius * v * progress;
    return [cx + Math.cos(a) * r, cy + Math.sin(a) * r];
  };
  const axisEnd = (i) => {
    const a = angle(i);
    return [cx + Math.cos(a) * radius, cy + Math.sin(a) * radius];
  };
  const labelPos = (i) => {
    const a = angle(i);
    const r = radius + 28;
    return [cx + Math.cos(a) * r, cy + Math.sin(a) * r];
  };

  const path = data.map((d, i) => {
    const [x, y] = point(i, d.value);
    return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(" ") + " Z";

  const rings = [0.25, 0.5, 0.75, 1];

  const hoverData = hover !== null ? data[hover] : null;

  return (
    <div className="radar-wrap" style={{ width: size, position: "relative" }}>
      {hoverData && (
        <div style={{
          position: "absolute", top: -8, left: "50%", transform: "translateX(-50%)",
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--r)", padding: "8px 12px",
          fontSize: 12, color: "var(--fg)", textAlign: "center",
          whiteSpace: "nowrap", zIndex: 10, pointerEvents: "none",
          boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
          animation: "float-in 0.2s ease",
          maxWidth: 260, whiteSpace: "normal",
        }}>
          <div style={{ fontFamily: "var(--f-display)", fontWeight: 600, color: color, marginBottom: 2 }}>
            {hoverData.label} — {hoverData.value.toFixed(2)}
          </div>
          <div style={{ color: "var(--fg-mute)", fontSize: 11, lineHeight: 1.4 }}>
            {RADAR_DESCRIPTIONS[hoverData.label] || ""}
          </div>
        </div>
      )}
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ overflow: "visible" }}>
        {/* Rings */}
        {rings.map((r, idx) => (
          <polygon key={idx}
            points={data.map((_, i) => {
              const a = angle(i);
              return `${cx + Math.cos(a) * radius * r},${cy + Math.sin(a) * radius * r}`;
            }).join(" ")}
            fill="none" stroke="var(--border)" strokeWidth="0.8" opacity={0.7 - idx * 0.1} />
        ))}
        {/* Axes */}
        {data.map((_, i) => {
          const [x, y] = axisEnd(i);
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--border)" strokeWidth="0.8" />;
        })}
        {/* Fill */}
        <path d={path}
          fill={color} fillOpacity="0.15"
          stroke={color} strokeWidth="1.6"
          style={{ filter: glow ? `drop-shadow(0 0 10px ${color})` : "none" }}/>
        {/* Points */}
        {data.map((d, i) => {
          const [x, y] = point(i, d.value);
          const isHover = hover === i;
          return (
            <g key={i}>
              <circle cx={x} cy={y} r={isHover ? 6 : 4}
                      fill={color}
                      style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: "r .15s" }}
                      onMouseEnter={() => setHover(i)}
                      onMouseLeave={() => setHover(null)}/>
            </g>
          );
        })}
        {/* Labels */}
        {data.map((d, i) => {
          const [x, y] = labelPos(i);
          const isHover = hover === i;
          const anchor = Math.cos(angle(i)) > 0.3 ? "start" : Math.cos(angle(i)) < -0.3 ? "end" : "middle";
          return (
            <g key={i} style={{ pointerEvents: "auto" }}
               onMouseEnter={() => setHover(i)}
               onMouseLeave={() => setHover(null)}>
              <text x={x} y={y} textAnchor={anchor} dominantBaseline="middle"
                fontFamily="var(--f-mono)" fontSize="10" letterSpacing="0.04em"
                fill={isHover ? color : "var(--fg-mute)"}
                style={{ textTransform: "uppercase" }}>{d.label}</text>
              <text x={x} y={y + 14} textAnchor={anchor} dominantBaseline="middle"
                fontFamily="var(--f-mono)" fontSize="11"
                fill={isHover ? "var(--fg)" : "var(--fg-dim)"}>
                {d.value.toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

Object.assign(window, { RadarChart });
