/* Navigation + Footer + Global Vibe Mode toggle + Theme toggle */

const { useState, useEffect } = React;

function ThemeToggle({ theme, setTheme }) {
  const isDark = theme !== "light";
  return (
    <button
      className="theme-toggle"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      ) : (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      )}
    </button>
  );
}

function NaijaVibeToggle({ vibe, setVibe, label }) {
  const [showBanner, setShowBanner] = useState(false);
  const t = (window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {};
  const displayLabel = label !== undefined ? label : (t.nav || {}).vibeMode || "Naija Vibe Mode";

  const handleToggle = () => {
    setVibe(!vibe);
    setShowBanner(true);
    setTimeout(() => setShowBanner(false), 2400);
  };

  // vibe is NEW value after toggle
  const bannerMsg = vibe
    ? "Naija mode don enter! 🔥"
    : "Back to English mode";

  return (
    <div style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
      <button
        className={`toggle ${showBanner ? "toggle-pulse" : ""}`}
        data-on={vibe ? "true" : "false"}
        onClick={handleToggle}
        aria-label={`Toggle Naija Vibe Mode — currently ${vibe ? "on" : "off"}`}
        aria-pressed={vibe}
      >
        <div className="toggle-track" aria-hidden="true">
          <div className="toggle-thumb"></div>
        </div>
        {displayLabel && (
          <span className="toggle-label" style={{ color: vibe ? "var(--amber)" : "var(--fg-mute)" }}>
            {displayLabel}
          </span>
        )}
      </button>
      {showBanner && (
        <div className="vibe-banner" aria-live="polite">
          {bannerMsg}
        </div>
      )}
    </div>
  );
}

function Nav({ route, navigate, vibe, setVibe, theme, setTheme }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const t = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).nav || {};

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => { setMobileOpen(false); }, [route]);

  const links = [
    { to: "/task-a",       label: t.generateReview   || "Generate Review" },
    { to: "/task-b",       label: t.recommendations  || "Recommendations" },
    { to: "/architecture", label: t.howItWorks       || "How It Works" },
    { to: "/paper",        label: t.paper            || "Our Paper" },
    { to: "/evaluation",   label: t.evaluation       || "Evaluation" },
  ];

  return (
    <nav className={`nav ${scrolled ? "scrolled" : ""}`} role="navigation" aria-label="Main navigation">
      <div className="container nav-inner">
        <a
          href="#/"
          onClick={(e) => { e.preventDefault(); navigate("/"); }}
          className="nav-logo"
          aria-label="Naiview Intelligence — Home"
        >
          <Logo />
        </a>

        <div className="nav-links" role="list">
          {links.map(l => (
            <a
              key={l.to}
              href={`#${l.to}`}
              role="listitem"
              className={`nav-link ${route === l.to ? "active" : ""}`}
              aria-current={route === l.to ? "page" : undefined}
              onClick={(e) => { e.preventDefault(); navigate(l.to); }}
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="nav-right">
          <ThemeToggle theme={theme} setTheme={setTheme} />
          <NaijaVibeToggle vibe={vibe} setVibe={setVibe} />
          <button
            className="nav-burger"
            onClick={() => setMobileOpen(o => !o)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            aria-controls="nav-mobile-menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              {mobileOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </>
              ) : (
                <>
                  <line x1="3" y1="6" x2="21" y2="6"/>
                  <line x1="3" y1="12" x2="21" y2="12"/>
                  <line x1="3" y1="18" x2="21" y2="18"/>
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div id="nav-mobile-menu" className="nav-mobile" role="list">
          <a
            href="#/"
            role="listitem"
            className={`nav-link ${route === "/" ? "active" : ""}`}
            aria-current={route === "/" ? "page" : undefined}
            onClick={(e) => { e.preventDefault(); navigate("/"); }}
          >
            {t.home || "Home"}
          </a>
          {links.map(l => (
            <a
              key={l.to}
              href={`#${l.to}`}
              role="listitem"
              className={`nav-link ${route === l.to ? "active" : ""}`}
              aria-current={route === l.to ? "page" : undefined}
              onClick={(e) => { e.preventDefault(); navigate(l.to); }}
            >
              {l.label}
            </a>
          ))}
          <div className="nav-mobile-vibe" style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <ThemeToggle theme={theme} setTheme={setTheme} />
            <NaijaVibeToggle vibe={vibe} setVibe={setVibe} />
          </div>
        </div>
      )}
    </nav>
  );
}

function Footer({ navigate, vibe }) {
  const t = ((window.TRANSLATIONS || {})[vibe ? "pidgin" : "en"] || {}).footer || {};
  return (
    <footer className="footer">
      <PatternBand color="var(--border)" />
      <div className="container footer-inner">
        <div className="footer-col">
          <Logo />
          <p className="dim" style={{ maxWidth: 320, marginTop: 12, fontSize: 14 }}>
            {t.tagline || "Culturally-aware LLM agent system. User modeling and recommendations, built around Nigerian behavioural patterns."}
          </p>
          <div className="mono" style={{ fontSize: 11, color: "var(--fg-faint)", marginTop: 16, letterSpacing: "0.12em" }}>
            {t.hackathon || "BUILT WITH 🇳🇬 FOR DSN × BCT HACKATHON 3.0"}
          </div>
        </div>
        <div className="footer-col">
          <div className="eyebrow" style={{ marginBottom: 12 }}>{t.explore || "Explore"}</div>
          <a className="footer-link" href="#/task-a" onClick={(e)=>{e.preventDefault();navigate("/task-a");}}>
            {t.generateReview || "Generate Review"}
          </a>
          <a className="footer-link" href="#/task-b" onClick={(e)=>{e.preventDefault();navigate("/task-b");}}>
            {t.getRecommendations || "Get Recommendations"}
          </a>
          <a className="footer-link" href="#/architecture" onClick={(e)=>{e.preventDefault();navigate("/architecture");}}>
            {t.howItWorks || "How It Works"}
          </a>
          <a className="footer-link" href="#/evaluation" onClick={(e)=>{e.preventDefault();navigate("/evaluation");}}>
            {t.evaluation || "Evaluation"}
          </a>
        </div>
        <div className="footer-col">
          <div className="eyebrow" style={{ marginBottom: 12 }}>{t.team || "Team"}</div>
          {[
            { name: "Testimony", color: "var(--teal)" },
            { name: "Aaliyah", color: "var(--amber)" },
            { name: "Shiloh", color: "var(--lavender)" },
          ].map(p => (
            <div key={p.name} className="footer-person">
              <Avatar name={p.name} color={p.color} size={28} ring={false} />
              <span style={{ fontSize: 14 }}>{p.name}</span>
            </div>
          ))}
        </div>
        <div className="footer-col">
          <div className="eyebrow" style={{ marginBottom: 12 }}>{t.resources || "Resources"}</div>
          <a className="footer-link" href="#/paper" onClick={(e)=>{e.preventDefault();navigate("/paper");}}>
            {t.paper || "Solution Paper"}
          </a>
          <a className="footer-link" href="#">{t.github || "GitHub Repository ↗"}</a>
          <a className="footer-link" href="#">{t.archDoc || "Architecture Doc ↗"}</a>
          <a className="footer-link" href="#">{t.dataset || "Dataset Strategy ↗"}</a>
        </div>
      </div>
      <div className="container footer-bottom">
        <span className="mono dim" style={{ fontSize: 11 }}>© 2026 Naiview Intelligence</span>
        <span className="mono dim" style={{ fontSize: 11 }}>v0.1 · Hackathon Build</span>
      </div>
    </footer>
  );
}

Object.assign(window, { Nav, Footer, NaijaVibeToggle, ThemeToggle });
