// Naiview Intelligence — Client Runtime Config
// -------------------------------------------------------
// Edit this file to point at your FastAPI backend.
// In a Vite build, set VITE_API_BASE_URL in .env instead.
//
// demoMode: true  → fall back to mock data if the API is unreachable
// demoMode: false → always hit the real API (fail loudly)

window.__NAIVIEW_CONFIG__ = {
  apiBaseUrl: "http://localhost:8000",
  demoMode: true,
};
