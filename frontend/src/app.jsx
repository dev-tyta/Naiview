/* APP — Router + Shell + API helper */

const { useState, useEffect } = React;

// ------------------------------------------------------------------
// API helpers — reads base URL from env.js (window.__NAIVIEW_CONFIG__)
// ------------------------------------------------------------------
async function apiPost(path, body) {
  const cfg = window.__NAIVIEW_CONFIG__ || {};
  const base = cfg.apiBaseUrl || "http://localhost:9000";
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => `HTTP ${res.status}`);
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiGet(path) {
  const cfg = window.__NAIVIEW_CONFIG__ || {};
  const base = cfg.apiBaseUrl || "http://localhost:9000";
  const res = await fetch(`${base}${path}`);
  if (!res.ok) {
    const text = await res.text().catch(() => `HTTP ${res.status}`);
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

function isDemoMode() {
  return (window.__NAIVIEW_CONFIG__ || {}).demoMode !== false;
}

// Expose globally so pages can use without React context plumbing
Object.assign(window, { apiPost, apiGet, isDemoMode });

// ------------------------------------------------------------------
// Hash router
// ------------------------------------------------------------------
function useHashRoute() {
  const [route, setRoute] = useState(() => (window.location.hash || "#/").slice(1) || "/");
  useEffect(() => {
    const onHash = () => setRoute((window.location.hash || "#/").slice(1) || "/");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const navigate = (to) => {
    window.location.hash = to;
    window.scrollTo({ top: 0, behavior: "instant" });
  };
  return [route, navigate];
}

// ------------------------------------------------------------------
// App root
// ------------------------------------------------------------------
function App() {
  const [route, navigate] = useHashRoute();
  const [vibe, setVibe] = useState(() => localStorage.getItem("naija-vibe") === "true");
  const [theme, setTheme] = useState(() => localStorage.getItem("naiview-theme") || "dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-vibe", vibe ? "on" : "off");
    localStorage.setItem("naija-vibe", vibe);
  }, [vibe]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("naiview-theme", theme);
  }, [theme]);

  const pageProps = { vibe, setVibe, navigate, theme, setTheme };

  let page;
  switch (route) {
    case "/":             page = <Landing {...pageProps} />; break;
    case "/task-a":       page = <TaskA {...pageProps} />; break;
    case "/task-b":       page = <TaskB {...pageProps} />; break;
    case "/architecture": page = <ArchitecturePage {...pageProps} />; break;
    case "/paper":        page = <PaperPage {...pageProps} />; break;
    case "/evaluation":   page = <EvaluationPage {...pageProps} />; break;
    default:              page = <Landing {...pageProps} />;
  }

  return (
    <>
      <Nav route={route} navigate={navigate} vibe={vibe} setVibe={setVibe} theme={theme} setTheme={setTheme} />
      <main key={route} className="page-enter" data-screen-label={route === "/" ? "Landing" : route.slice(1)}>
        {page}
      </main>
      <Footer navigate={navigate} vibe={vibe} />
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
