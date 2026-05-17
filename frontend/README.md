# Naiview Intelligence — Frontend Prototype

A culturally-aware LLM agent system for the **DSN × BCT Hackathon 3.0**. This package is the production-grade design + working prototype for the frontend, structured so it can be handed directly to Claude Code (or any frontend dev) for full implementation and FastAPI integration.

> Open `Naiview Intelligence.html` in a browser to see all six pages live, with mock data wired through. Nothing to install.

## What's in this package

```
.
├── Naiview Intelligence.html     # Single-entry SPA, hash-routed
├── src/
│   ├── styles.css                # Design tokens (colors, type, motion)
│   ├── components.css            # Component-scoped styles
│   ├── app.jsx                   # Router + Vibe Mode state
│   ├── components/
│   │   ├── shared.jsx            # Stars, Chip, MetricRing, Avatar, Reveal, Logo
│   │   ├── nav.jsx               # Nav, Footer, NaijaVibeToggle 
│   │   └── radar.jsx             # 7-axis radar chart
│   └── pages/
│       ├── landing.jsx           # 6-section storytelling hero
│       ├── task-a.jsx            # Review generation workbench
│       ├── task-b.jsx            # Recommendations + cold-start chat
│       ├── architecture.jsx      # Scrollytelling system walkthrough
│       ├── paper.jsx             # Solution paper + resources
│       └── evaluation.jsx        # Metrics dashboard + side-by-side
├── README.md
└── HANDOFF.md                    # Claude Code instructions (read this!)
```

## The pages

| # | Route | Purpose |
|---|---|---|
| 1 | `/`              | Landing — scrollytelling hero (Hook → Problem → Solution → Manifesto → Team → CTA) |
| 2 | `/task-a`        | Task A — Review Generation. Persona + product → review, rating, fingerprint, reasoning trace |
| 3 | `/task-b`        | Task B — Recommendations + cold-start 3-turn chat |
| 4 | `/architecture`  | How It Works — 5 animated scenes walking through the agent |
| 5 | `/paper`         | Solution paper download + supplementary docs + GitHub card |
| 6 | `/evaluation`    | Metrics dashboard + side-by-side cultural comparison tool |

## Design system

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0D0D0F` | App background |
| `--surface` | `#161619` | Cards, panels |
| `--border` | `#2A2A2E` | 1px lines, inactive chrome |
| `--teal` | `#00D4AA` | Primary accent — CTAs, active states, high confidence |
| `--amber` | `#E8A838` | Nigerian/cultural accent — stars, vibe mode, manifesto |
| `--lavender` | `#8B7EC8` | Tertiary — categories, secondary UI |
| `--rose` | `#D4566A` | Low confidence, errors |
| `--fg` | `#E8E6E3` | Primary text (warm off-white) |
| `--fg-mute` | `#7A7A80` | Secondary text, labels |

**Type:** Space Grotesk (display) · Manrope (body) · JetBrains Mono (code/accent)

**Motion:** Reveal-on-scroll, typewriter cursor for review output, radar draw-in, scroll-triggered architecture scenes, pulse-glow for Vibe Mode toggle.

## Global behaviors

- **Naija Vibe Mode** — global toggle in nav. Switches review output register (Pidgin vs standard English) and accent hints. State persists in `localStorage`.
- **Hash routing** — clean URLs like `#/task-a`, scrolls to top on navigation.
- **Mock data** — every page is wired with realistic Nigerian content (personas, businesses, Pidgin reviews). Swap for live API in implementation.

## Running locally

Just open `Naiview Intelligence.html` in a browser. The Babel standalone transformer compiles JSX in the browser — no build step. Fonts and React are loaded from CDN.

For production, see `HANDOFF.md` for the Vite/Next migration plan.


