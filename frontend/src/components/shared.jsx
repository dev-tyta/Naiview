/* Shared primitives — Stars, Chip, ConfidenceMeter, Reveal, Avatar, ErrorBanner */

const { useEffect, useRef, useState } = React;

function Stars({ value = 0, max = 5, size = 18 }) {
  return (
    <span className="stars" aria-label={`${value} out of ${max} stars`} role="img">
      {Array.from({ length: max }).map((_, i) => {
        const filled = i + 1 <= Math.floor(value);
        const half = !filled && i < value;
        return (
          <svg
            key={i}
            className={`star ${filled || half ? "on" : ""}`}
            width={size} height={size}
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M12 2.5l2.95 6.6 7.2.75-5.4 4.85 1.55 7.05L12 18.1l-6.3 3.65 1.55-7.05L1.85 9.85l7.2-.75L12 2.5z" />
          </svg>
        );
      })}
    </span>
  );
}

function confLevel(v) {
  if (v >= 0.85) return "high";
  if (v >= 0.70) return "med";
  return "low";
}

function ConfidenceChip({ value, label = "Confidence" }) {
  const level = confLevel(value);
  return (
    <span className={`chip ${level}`} title={`${label}: ${value.toFixed(2)}`}>
      <span className="chip-dot" aria-hidden="true"></span>
      <span>{label}</span>
      <span className="mono" style={{ marginLeft: 4 }}>{value.toFixed(2)}</span>
    </span>
  );
}

function MetricRing({ value, label, hint, invert = false, size = 140 }) {
  const display = invert ? (1 - value).toFixed(2) : value.toFixed(2);
  const pct = invert ? (1 - value) : value;
  const r = size / 2 - 10;
  const c = 2 * Math.PI * r;
  const dash = c * pct;
  const color = pct >= 0.75 ? "var(--teal)" : pct >= 0.5 ? "var(--amber)" : "var(--rose)";
  return (
    <div className="metric-ring" aria-label={`${label}: ${display}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--border)" strokeWidth="6" />
        <circle cx={size/2} cy={size/2} r={r} fill="none"
                stroke={color} strokeWidth="6" strokeLinecap="round"
                strokeDasharray={`${dash} ${c}`}
                transform={`rotate(-90 ${size/2} ${size/2})`}
                style={{ filter: `drop-shadow(0 0 8px ${color})`, transition: "stroke-dasharray 1.2s ease" }} />
        <text x={size/2} y={size/2 - 2} textAnchor="middle" fontFamily="JetBrains Mono"
              fontSize="22" fill="var(--fg)" fontWeight="500">{invert ? value.toFixed(2) : display}</text>
        <text x={size/2} y={size/2 + 18} textAnchor="middle" fontFamily="JetBrains Mono"
              fontSize="9" fill="var(--fg-mute)" letterSpacing="2">SCORE</text>
      </svg>
      <div className="metric-meta">
        <div className="metric-label">{label}</div>
        {hint && <div className="metric-hint">{hint}</div>}
      </div>
    </div>
  );
}

function Reveal({ children, delay = 0, as = "div", className = "" }) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    // Respect reduced-motion: skip animation, show immediately
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(true);
      return;
    }
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setShown(true); io.disconnect(); }
    }, { threshold: 0.12 });
    if (ref.current) io.observe(ref.current);
    return () => io.disconnect();
  }, []);
  const Tag = as;
  return (
    <Tag
      ref={ref}
      className={`reveal ${shown ? "in" : ""} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  );
}

function Avatar({ name, color = "var(--teal)", size = 96, ring = true }) {
  const initials = name.split(/\s+/).map(s => s[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div className="avatar-wrap" style={{ width: size, height: size }} aria-hidden="true">
      {ring && (
        <div className="avatar-ring" style={{
          background: `conic-gradient(from 0deg, ${color}, transparent 40%, ${color})`,
        }}></div>
      )}
      <div className="avatar" style={{
        width: size - 8, height: size - 8,
        background: `linear-gradient(135deg, color-mix(in oklab, ${color} 25%, var(--surface)) 0%, var(--surface) 100%)`,
        color: color,
        fontFamily: "var(--f-display)",
        fontSize: size * 0.32,
        fontWeight: 500,
      }}>{initials}</div>
    </div>
  );
}

function PatternBand({ color = "var(--teal)" }) {
  return (
    <svg width="100%" height="20" preserveAspectRatio="none" style={{ display: "block", opacity: 0.5 }} aria-hidden="true">
      <defs>
        <pattern id={`adire-${color.replace(/[^a-zA-Z0-9]/g, "")}`} x="0" y="0" width="14" height="14" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1" fill={color} opacity="0.6" />
          <circle cx="9" cy="9" r="0.8" fill={color} opacity="0.3" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#adire-${color.replace(/[^a-zA-Z0-9]/g, "")})`} />
    </svg>
  );
}

function Logo({ size = 24 }) {
  return (
    <div className="logo" aria-label="Naiview Intelligence">
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <path d="M6 24V8h3l9 11V8h3v16h-3L9 13v11H6z" fill="var(--fg)"/>
        <circle cx="26" cy="9" r="3" fill="var(--teal)" style={{ filter: "drop-shadow(0 0 6px var(--teal-glow))" }}/>
      </svg>
      <span style={{ fontFamily: "var(--f-display)", fontWeight: 500, fontSize: 18, letterSpacing: "-0.02em" }}>Naiview</span>
    </div>
  );
}

// Error banner for API failures
function ErrorBanner({ message, onRetry, label = "Error" }) {
  if (!message) return null;
  return (
    <div className="error-banner" role="alert" aria-live="assertive">
      <div className="error-banner-inner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--rose)" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span className="error-banner-label">{label}:</span>
        <span className="error-banner-msg">{message}</span>
      </div>
      {onRetry && (
        <button className="btn btn-sm error-retry" onClick={onRetry}>
          ↻ Retry
        </button>
      )}
    </div>
  );
}

// Skeleton shimmer line
function SkeletonLine({ width = "100%", height = 14, style = {} }) {
  return (
    <div
      className="skeleton-line"
      style={{ width, height, ...style }}
      aria-hidden="true"
    />
  );
}

Object.assign(window, { Stars, ConfidenceChip, MetricRing, Reveal, Avatar, PatternBand, Logo, confLevel, ErrorBanner, SkeletonLine });
