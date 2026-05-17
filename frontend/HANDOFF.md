# Claude Code Handoff — Naiview Intelligence Frontend

> **Read this first.** This document tells you exactly how to take the design prototype in this folder and turn it into a production-grade React app wired to the FastAPI backend.

---

## What you're working from

The folder you're holding is a **fully designed, fully interactive HTML+JSX prototype** of every screen in the Naiview Intelligence frontend. It uses in-browser Babel for zero-build iteration. It includes:

- All design tokens (colors, typography, spacing, motion)
- All six pages with mock data flowing through
- All components (radar chart, reasoning trace, chat, comparison, metrics)
- All copywriting (Pidgin reviews, sample recs, manifesto)
- All hover/active/loading states

**Your job is to migrate this 1:1 to a production React app and wire it to live FastAPI endpoints.**

---

## Migration target

**Stack:**
- **Vite + React 18 + TypeScript** (recommended) OR Next.js 14 App Router
- **Tailwind CSS** — for utilities. Keep `styles.css` for design tokens via `@layer base`
- **React Router v6** (Vite) or built-in routing (Next)
- **Recharts** (or keep the hand-rolled SVG radar — it's already polished)
- **react-query / TanStack Query** — for API state
- **Zod** — for API response validation
- **Framer Motion** — replace the IntersectionObserver `Reveal` and CSS animations with Framer's `motion` primitives where smoother control is needed (architecture scrollytelling especially)

**Suggested folder structure:**
```
src/
├── main.tsx
├── App.tsx                    # Router + AppShell
├── shell/
│   ├── Nav.tsx
│   ├── Footer.tsx
│   └── NaijaVibeContext.tsx   # Global vibe mode state (was localStorage in prototype)
├── pages/
│   ├── Landing.tsx
│   ├── TaskA.tsx
│   ├── TaskB.tsx
│   ├── Architecture.tsx
│   ├── Paper.tsx
│   └── Evaluation.tsx
├── components/
│   ├── RadarChart.tsx
│   ├── ReasoningTrace.tsx
│   ├── ReviewCard.tsx
│   ├── RecommendationCard.tsx
│   ├── ColdStartChat.tsx
│   ├── ConfidenceChip.tsx
│   ├── Stars.tsx
│   ├── MetricRing.tsx
│   └── primitives/            # Button, Card, Input, Toggle
├── api/
│   ├── client.ts              # axios/fetch wrapper with base URL
│   ├── taskA.ts
│   ├── taskB.ts
│   └── types.ts               # TS interfaces matching FastAPI response shapes
├── lib/
│   └── reveal.tsx             # InView/Framer-based reveal wrapper
└── styles/
    ├── tokens.css             # Copy of src/styles.css :root vars
    └── globals.css            # Tailwind + base styles
```

---

## API integration

Three endpoints to wire. Match the exact request/response shapes below.

### `POST /task-a/generate`
```ts
// Request
{ user_id?: string;
  persona?: string;        // mutually exclusive with user_id
  item_metadata: {
    name: string;
    category: string;
    description?: string;
  };
  naija_vibe_mode: boolean;
}

// Response
{ review_text: string;
  rating: number;          // 1.0 – 5.0, half-stars allowed
  confidence: number;      // 0.0 – 1.0
  vibe_score: number;      // 0.0 – 1.0
  fingerprint: { dimension: string; value: number }[]; // 7 entries
  fingerprint_match: string;
  style_notes: string;
  reasoning_trace: { step: number; title: string; detail: string }[];
}
```

**Wire location:** `src/pages/task-a.jsx` → `generate()` function.

### `POST /task-b/recommend`
```ts
// Request
{ user_id?: string;
  persona?: string;
  category?: string;
  mood?: string;
  naija_vibe_mode: boolean;
}

// Response
{ recommendations: {
    name: string;
    category: string;
    match_score: number;     // 0 – 100
    confidence: number;      // 0.0 – 1.0
    explanation: string;     // Naija-flavoured if vibe_mode
  }[];
  diversity_score: number;
  diversity_breakdown: { dimension: string; value: number }[];
  reasoning_trace: { step: number; title: string; detail: string }[];
}
```

### `POST /task-b/cold-start`
```ts
// Request
{ session_id: string;
  turn_number: number;       // 0, 1, 2
  user_response?: string;    // null on turn 0 (agent kicks off)
  naija_vibe_mode: boolean;
}

// Response
{ agent_message: string;
  next_turn: number;
  done: boolean;             // true after turn 3
  recommendations?: Recommendation[];  // present when done = true
}
```

**Wire location:** `src/pages/task-b.jsx` → `startColdStart()` + `sendUserMessage()`.

---

## Loading / error states

Each task page needs three states. Loading is already designed (the `cursor` blinking text). Add:

- **Skeleton state** while data loads (use Tailwind's `animate-pulse`)
- **Error toast** for API failures — match the design system: dark surface, rose accent, JetBrains Mono label
- **Retry button** in error state

Pattern (TS):
```tsx
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ["task-a", payload],
  queryFn: () => api.taskA.generate(payload),
  enabled: false,
});
```

---

## State you must preserve

| State | Where | How |
|---|---|---|
| Naija Vibe Mode | Global | React Context + `localStorage` persistence |
| Cold-start session | Task B | `sessionStorage` keyed by random `session_id` |
| Hash route | Global | React Router |
| Form inputs (persona, item) | Page-local | `useState`, no need to persist |
| Tweaks/comparisons index | Evaluation | Page-local |

---

## What to keep 1:1 from the prototype

- **All copywriting.** The manifesto, sample reviews, beat text, mock recs — all of it. Don't paraphrase.
- **The color palette.** Don't drift the teal toward green, the amber toward orange. Use the exact hex values.
- **Type pairing.** Space Grotesk + Manrope + JetBrains Mono. Substitution will collapse the aesthetic.
- **The radar chart.** It's already production-quality. Just port `src/components/radar.jsx` to TSX.
- **The reasoning trace.** Same — port verbatim, type the props.
- **All micro-animations** — typewriter, reveal-on-scroll, vibe-toggle pulse, radar draw-in.

## What to upgrade

- **Architecture scrollytelling.** The prototype uses simple Reveal. Production should drive node-graph progress from scroll position using `useScroll` + `useTransform` from Framer Motion.
- **Side-by-side comparison.** Add word-by-word animated text reveal (the prompt called for this).
- **Cold-start chat.** Make typing indicator timing configurable; consider streaming the agent message via SSE.
- **Hero background.** Promote the SVG glow orbs to WebGL (Three.js) for a richer effect — optional.

---

## Implementation checklist

```
☐ Bootstrap Vite + React + TS + Tailwind
☐ Copy src/styles.css tokens into Tailwind theme.extend (colors, fontFamily, borderRadius)
☐ Port src/components/shared.jsx → src/components/primitives/*.tsx
☐ Port nav.jsx, radar.jsx
☐ Port each page from src/pages/*.jsx → src/pages/*.tsx
☐ Replace mock data with TanStack Query hooks
☐ Set up api/ client with env-based base URL (VITE_API_URL)
☐ Wire NaijaVibeContext globally (replace useState in prototype)
☐ Add error/loading/empty states for each task page
☐ Set up Framer Motion for architecture scrollytelling
☐ Add Zod validation on API responses
☐ Configure CORS on FastAPI side (Allow VITE dev origin)
☐ Write unit tests for RadarChart, ReasoningTrace, ColdStartChat state machine
☐ Add OG meta tags for share preview
☐ Set up Vercel/Netlify deploy with env vars
☐ Configure analytics (Plausible/PostHog) — track Vibe Mode toggle, downloads, CTA clicks
```

---

## Backend notes for the agent system

This frontend assumes the FastAPI backend supports:

- **CORS** open to the frontend origin
- **Streaming** (optional, for typewriter SSE)
- A **persona embedding endpoint** if you want to render the radar BEFORE a generation call (snappier UX): `POST /persona/fingerprint`
- **Cold-start session storage** on the backend so the agent has conversation memory across turns

---

## Brand guardrails (DO / DON'T)

✅ **DO** — keep the dark IDE/terminal aesthetic. The darkness is the design.
✅ **DO** — use Pidgin in Naija Vibe Mode outputs. Keep it authentic, never cartoonish.
✅ **DO** — keep mono font for code, data values, and Pidgin phrases — it makes culture feel intentional.
✅ **DO** — show the reasoning trace prominently. It's how we prove the agent isn't a black box.

❌ **DON'T** — add the Nigerian flag colors (bright green/white) anywhere except the footer ❤️.
❌ **DON'T** — water down the manifesto. The pull quote is the emotional anchor of the entire site.
❌ **DON'T** — use Inter or any other system-default font.
❌ **DON'T** — make the Naija Vibe Mode toggle subtle. It should feel like a signature interaction.

---

Built for **Testimony · Aaliyah · Shiloh** — DSN × BCT Hackathon 3.0.
