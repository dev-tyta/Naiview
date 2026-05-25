// Naiview Intelligence — Client Runtime Config
// -------------------------------------------------------
// Edit this file to point at your FastAPI backend.
// In a Vite build, set VITE_API_BASE_URL in .env instead.
//
// demoMode: true  → fall back to mock data if the API is unreachable
// demoMode: false → always hit the real API (fail loudly)

window.__NAIVIEW_CONFIG__ = {
  apiBaseUrl: "https://naiview-production.up.railway.app",
  demoMode: true,

  // Solution paper Drive links
  paperLinkA: "https://drive.google.com/file/d/1V1i6cJk-g27ubXJcRL-k6-sUOe-vE31p/view?usp=drivesdk",
  paperLinkB: "https://drive.google.com/file/d/1-Z4ehj0DYbq1uzDF832UKuIbgMpfyUyu/view?usp=drivesdk",
};
