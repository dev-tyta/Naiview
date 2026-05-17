# Naiview Intelligence — Web UI Design Prompt

> **Purpose:** Paste this prompt into a new Claude conversation (or Claude artifact session) to generate the full frontend design for the Naiview Intelligence hackathon project.

---

## THE PROMPT

```
You are designing and building a production-grade, interactive web application for "Naiview Intelligence" — a culturally-aware LLM agent system built for the DSN x BCT Hackathon 3.0. This is a Nigerian AI project, and the design must reflect that identity with pride, sophistication, and authenticity — not as decoration, but as DNA.

## WHAT THIS APPLICATION DOES

NaijaReview Intelligence is a two-task LLM agent system:

**Task A — User Modeling (Review Generation)**
Takes a user persona + product details as input → generates realistic Nigerian-style reviews and star ratings. The agent uses a 7-dimensional behavioural fingerprint, cultural context, and a Naija Vibe Checker to produce outputs that sound authentically Nigerian.

**Task B — Recommendation Engine**
Takes a user persona as input → produces personalised recommendations with reasoning. Handles cold-start users through a conversational 3-turn onboarding flow. Supports cross-domain recommendations (restaurants, electronics, books, etc).

## THE PAGES / VIEWS TO DESIGN

### 1. Landing Page — Storytelling Hero Experience

This is NOT a generic hero with a tagline. It's a scroll-driven narrative that pulls the judge into our world before they touch a single button.

**Section A — The Hook (viewport 1)**
- Large cinematic text: "Naiview Intelligence"
- Subtitle fades in: "What if AI actually understood how Nigerians think, talk, and choose?"
- A subtle background animation — abstract shapes morphing between adire patterns and data network nodes (culture meets technology)
- Competition badge in corner: "DSN x BCT LLM Agent Challenge 3.0 | May 2026"
- Scroll indicator: a gentle bouncing arrow or "Scroll to see why this matters"

**Section B — The Problem (scroll-triggered)**
- Story unfolds in 3 beats with staggered fade-in animations:
  - Beat 1: "Every day, millions of Nigerians leave reviews, rate products, and make choices online."
  - Beat 2: "But the AI systems that analyse them? Built on American data, trained on Western patterns, tested on English that sounds nothing like us."
  - Beat 3: "A Lagos foodie who writes 'this jollof hit different — proper party vibes' gets flattened into the same profile as someone in Ohio who writes 'the food was great.'"
- Visual: side-by-side contrast — a generic AI output vs a culturally-aware one. The generic side is dimmed and desaturated; the Naiview side glows with teal accents and feels alive.
- Transition text: "We decided to fix this."

**Section C — The Solution (scroll-triggered)**
- "Naiview Intelligence is the first user modelling system built from the ground up around Nigerian behavioural patterns."
- Two animated cards slide in from left and right:
  - Card 1: "Task A — Review Generation" with a brief one-liner and a mini preview (a review card with Pidgin text and star rating)
  - Card 2: "Task B — Smart Recommendations" with a one-liner and mini preview (recommendation cards with match percentages)
- Below the cards, a horizontal animated strip showing the 7 fingerprint dimensions as icons with labels, scrolling gently

**Section D — "Why Culture Is Architecture, Not Decoration" Manifesto (scroll-triggered)**
This is the emotional anchor. It makes the judge understand this isn't decoration.
- Heading: "Why Culture Is Architecture, Not Decoration"
- 3-4 short storytelling paragraphs (NOT bullet points) explaining:
  - Nigerian reviewers show a bimodal rating pattern — 5 stars when happy, 1 star when angry. Western models expect a bell curve. If your AI assumes that curve, it misreads every Nigerian user.
  - A Kano user reviewing suya writes completely differently from a Port Harcourt user reviewing seafood. Region isn't metadata — it's identity.
  - "E sweet die" and "The food was excellent" carry the same sentiment but wildly different cultural signals. An AI that treats them the same understands neither.
  - "We didn't build a recommendation engine and add Nigerian flavour. We built Nigerian intelligence and gave it an engine."
- This section should feel editorial — like a beautifully typeset magazine article. Large pull quotes, generous spacing, subtle parallax scroll effect.

**Section E — Meet the Team (scroll-triggered)**
- Heading: "Built by people who get it"
- Three team member cards arranged horizontally (stacked on mobile), each with:
  - **Profile image** (circular, with a subtle animated border — a gradient ring that slowly rotates or a soft glow pulse). Design the placeholder to look intentional even without real photos — use styled initials avatar with each member's signature color. Leave clear `src` attributes so real photos drop in easily.
  - **Name** (bold): "Testimony" / "Aaliyah" / "Shiloh"
  - **Role tagline**: e.g., "Agent Architecture & ML Engineering" / "Memory Systems & Data Pipeline" / "Nigerian Language Module & Cultural Research"
  - **Personal quote** (italic or accent font): e.g., "I wanted to build AI that sounds like the people I grew up with." / "The data gap isn't a limitation — it's an opportunity to be original." / "If the vibe check fails, we don't ship it."
- Cards have a subtle hover animation — slight tilt/parallax or border glow intensifies
- Below the team cards: "Three builders. One mission. Make AI that actually gets us."

**Section F — Try It Yourself (CTAs)**
- Two prominent buttons:
  - "Generate a Review →" (routes to Task A)
  - "Get Recommendations →" (routes to Task B)
- Below: smaller links — "Read Our Solution Paper ↓" and "Explore the Architecture →"

### 2. Task A — Review Generation Interface
- **Input Panel:**
  - User ID field OR "Describe a persona" free-text input (e.g. "A picky Lagos foodie who loves amala")
  - Product/Item details input (name, category, description)
  - "Naija Vibe Mode" toggle switch (prominent, styled with brand accent colors)
  - "Generate Review" button
- **Output Panel:**
  - Generated review text displayed in a card with a speech-bubble or review-card aesthetic
  - Predicted star rating (visual stars, not just a number)
  - Confidence score (color-coded: green ≥0.85, amber 0.70–0.84, red <0.70)
  - Fingerprint match indicator (text: "High — user frequently reviews grills and street food")
  - Style notes (text: "User prefers short, punchy reviews")
- **Behavioural Fingerprint Radar Chart:**
  - 7 dimensions displayed as a radar/spider chart: Generosity, Verbosity, Emotional Intensity, Topic Focus, Consistency, Recency Weight, Nigerian Slang Index
  - Animated on load, interactive on hover (show dimension values)
- **Reasoning Trace (collapsible):**
  - Step-by-step display of the agent's reasoning chain:
    1. "Identified reviewer type: Street food enthusiast, Lagos-based"
    2. "Category match: 92% — user has reviewed 14 similar spots"
    3. "Predicted sentiment: Positive (based on category affinity)"
    4. "Generated in Pidgin-heavy register (slang index: 0.78)"
    5. "Vibe Check passed: 0.84 — authentic Nigerian tone confirmed"

### 3. Task B — Recommendation Interface
- **Input Panel:**
  - User ID field OR persona description
  - Optional: "What are you in the mood for?" free-text
  - Category selector (Food, Electronics, Books, Entertainment, etc)
  - "Get Recommendations" button
- **Output Panel:**
  - Recommendation cards (3-5 items) with:
    - Item name, category, match score
    - Personalised explanation in Nigerian voice ("Based on your love for spicy food and your budget consciousness, this one go sweet you...")
    - Confidence indicator per recommendation
  - Overall diversity score visualization
  - Reasoning chain (collapsible, like Task A)
- **Cold-Start Onboarding Flow:**
  - When user has no history, trigger a chat-style 3-turn conversation:
    - Turn 1: "Omo, welcome! Quick one — what kind of food do you normally enjoy?"
    - Turn 2: "Nice! Are you someone that values taste above everything, or does price/value matter more?"
    - Turn 3: "Got you. Last one — do you prefer busy lively spots or quieter places?"
  - Chat bubbles with Nigerian-flavoured agent responses
  - After 3 turns, smoothly transition to showing recommendations

### 4. Architecture / How It Works Page — Scrollytelling Experience
- NOT a static diagram dump. This is an animated, scroll-driven walkthrough of the system.
- **Scene 1 — "A request arrives"**: Show a simple input (user ID + item) entering the system. Animate it flowing into the API layer.
- **Scene 2 — "The agent starts thinking"**: The LangGraph state machine lights up node by node. Each node has a tooltip explaining what it does (fingerprinting, retrieval, reasoning, vibe check). Use a flowchart/node-graph visual that animates step by step as the user scrolls.
- **Scene 3 — "The shared brain"**: Zoom into the infrastructure layer — ChromaDB for memory, FAISS for item search, the Nigerian Language Module, the LLM Router. Each component fades in with a one-sentence explanation.
- **Scene 4 — "Culture runs through everything"**: Highlight the Nigerian Language Module specifically — AfriSenti phrase library, Pidgin mapper, region detector, code-switching patterns. Show example transformations: "The food was excellent" → "This food sweet die, I no go lie"
- **Scene 5 — "The output"**: The complete response assembles — review text, rating, confidence score, vibe score, reasoning trace — all sliding into place like puzzle pieces.
- At the bottom: a horizontal tech stack bar showing logos/icons: LangGraph, LangChain, ChromaDB, FAISS, FastAPI, Claude API, React, Docker

### 5. Solution Paper & Resources Page
- Heading: "Our Research & Documentation"
- Subheading: "The solution paper is the primary talent signal — it's what judges read first."

- **Solution Paper Download Section:**
  - A beautifully styled document preview card showing the paper's first page or a custom cover design (title, authors, abstract snippet)
  - Large download button: "Download Solution Paper (PDF)" with a file size indicator
  - Paper metadata displayed cleanly: Title, Authors (Testimony, Aaliyah, Shiloh), Page count, Date
  - A brief abstract or executive summary (3-4 sentences) visible on the page so judges can preview before downloading

- **Supplementary Downloads:**
  - Styled as a clean card grid (2-3 cards):
    - "Technical Architecture Document" — PDF download — "The full 1,773-line internal engineering specification"
    - "Dataset Strategy & Sources" — PDF download — "Our three-layer data strategy: structural backbone, Nigerian language calibration, synthetic augmentation"
    - "Evaluation Results" — PDF download — "ROUGE, BERTScore, NDCG@10, and human evaluation results"
  - Each card has: document icon, title, one-line description, file format badge (PDF), download button

- **Code Repository Link:**
  - A prominent GitHub card with repo name, star count placeholder, and "View on GitHub →" button
  - Below it: key repo stats — file count, test coverage, language breakdown (shown as a mini bar)

- **Quick Stats Bar** (horizontal, icon-driven):
  - "95 files scaffolded" | "16 LangChain tools" | "8 prompt templates" | "7 fingerprint dimensions" | "3 evaluation metrics"

### 6. Evaluation & Live Playground Page
This page lets judges see the system's quality metrics AND interact with it beyond the main Task A/B flows.

- **Evaluation Dashboard (top half):**
  - Heading: "How Good Is It? Let the Numbers Talk."
  - Metric cards in a grid:
    - ROUGE-L Score (with a gauge/progress ring visualization)
    - BERTScore (gauge)
    - Rating RMSE (gauge — lower is better, so invert the visual)
    - NDCG@10 (gauge)
    - Naija Vibe Score — average across test set (gauge)
    - Human Eval Score placeholder
  - Each metric card has: the score prominently displayed, a brief one-line explanation of what it measures, and a comparison note ("vs baseline: +12%")

- **Side-by-Side Comparison (bottom half):**
  - Heading: "See the Difference Culture Makes"
  - A split-screen comparison tool:
    - Left panel: "Generic Mode" — shows a review/recommendation generated WITHOUT Nigerian cultural intelligence
    - Right panel: "Naija Vibe Mode" — shows the same request processed WITH full cultural pipeline
    - Same input for both, dramatically different outputs
    - A "Try Another" button that cycles through 5-6 pre-loaded comparison examples
  - This is the single most persuasive visual in the entire application — it proves the thesis in 3 seconds

### 7. Global Elements

**Navigation Bar:**
- Fixed/sticky at top, transparent on the landing page hero, solid on scroll
- Logo: "Naiview" with a small stylized icon (maybe a chat bubble with a Nigerian flag accent, or a fingerprint icon with brand colors)
- Nav links: Home | Generate Review | Get Recommendations | How It Works | Our Paper | Evaluation
- A persistent "Naija Vibe Mode" global toggle in the nav (when activated, it subtly shifts the entire app's accent colors and loading messages to Nigerian mode)

**Footer:**
- Clean, minimal footer with:
  - Project name and competition credit
  - Team names with small profile avatars (linking back to the team section)
  - GitHub repo link
  - "Built with 🇳🇬 for DSN x BCT Hackathon 3.0"
  - A subtle adire-inspired line pattern in muted grey as the footer border/accent

## DESIGN DIRECTION

### Aesthetic: "Dark Intelligence" — Moody, Techy, Premium
This is NOT a generic SaaS dashboard and NOT a bright-green-and-gold Nigerian flag tribute. This is a sophisticated AI product that happens to be deeply Nigerian — think developer tool meets editorial publication meets Lagos-at-midnight energy. The darkness makes the data glow. The restraint makes the culture hit harder when it appears.

### Color Palette — Dark, Dim, Techy
- **Base/Background:** Deep charcoal-black (#0D0D0F) with very subtle blue undertone — not pure black, more like a dark IDE or terminal background
- **Surface/Cards:** Slightly elevated dark (#161619) with soft 1px borders in muted grey (#2A2A2E) — layered depth without harsh contrast
- **Primary Accent:** Electric teal/cyan (#00D4AA) — the signature color. Used sparingly for CTAs, active states, chart highlights, and key data points. It should feel like a cursor blinking in a terminal — precise, alive, techy.
- **Secondary Accent:** Warm amber (#E8A838) — used for Nigerian cultural elements, vibe scores, star ratings, and the Naija Vibe Mode toggle glow. This is the "warmth in the dark" — culture showing through the tech.
- **Tertiary/Subtle:** Muted lavender (#8B7EC8) — for secondary UI elements, tags, category badges, and the reasoning trace step indicators
- **Text Primary:** Off-white (#E8E6E3) — warm enough to not feel clinical against the dark background
- **Text Secondary:** Muted grey (#7A7A80) — for labels, descriptions, metadata
- **Confidence colors:** Teal (#00D4AA) for high confidence, amber (#E8A838) for medium, muted rose (#D4566A) for low
- **Glow effects:** The teal accent should have a soft glow/bloom effect on hover and active states — like neon reflecting off wet Lagos streets at night. Use `box-shadow` with teal at low opacity for buttons, active cards, and chart elements.
- **Gradients:** Subtle dark-to-darker gradients for section backgrounds. For special moments (hero section, Naija Vibe Mode activation), use a very faint teal-to-amber gradient that barely registers — atmospheric, not decorative.
- Avoid: bright greens, Nigerian flag literal colors, white backgrounds, any palette that looks like a government website or a generic fintech app

### Typography
- Display/Headings: Something sharp and modern that pops on dark backgrounds — consider fonts like "Clash Display", "Satoshi", "Syne", "Space Grotesk", or "Manrope" (choose ONE that feels premium and technical). The display font should feel confident at large sizes against the dark background.
- Body: A clean, highly readable sans-serif optimized for light-on-dark reading — generous letter-spacing, comfortable line height
- Accent/Code: For Nigerian phrases, data values, and technical labels, use a monospace or semi-mono font (like "JetBrains Mono" or "Fira Code") to give a developer-tool feel. Pidgin phrases rendered in mono feel intentional and distinctive rather than decorative.
- NO Inter, Roboto, Arial, or system defaults

### Visual Language
- Subtle geometric patterns inspired by Nigerian textile motifs (adire, ankara) rendered as faint line art or dot patterns in muted grey (#2A2A2E) on the dark background — they should be barely visible until you look closely, like watermarks. NOT colorful or heavy-handed.
- Generous dark space — let the darkness breathe. Content islands floating in dark negative space feel premium.
- Cards with subtle border glow on hover (teal or amber depending on context), very slight border-radius (8-12px)
- Micro-animations: radar chart drawing itself in with teal glow, confidence scores counting up with number color shifting from grey to teal, review text appearing with a typewriter cursor effect
- The Naija Vibe Mode toggle should be a signature moment — when activated, it pulses amber, and the entire page's accent hints shift from pure teal to a teal-amber blend. Maybe a subtle particle effect or a warm glow pulse radiates outward from the toggle.
- Star ratings custom-styled in amber with a soft glow
- Data visualizations (radar chart, gauges, comparison panels) should use the teal/amber/lavender palette against dark backgrounds — they should feel like monitoring dashboards or mission control displays

### Key UI Patterns
- Frosted glass / glass-morphism cards with dark semi-transparent backgrounds (rgba(22,22,25,0.8)) and subtle backdrop-blur — content floats above the base layer
- Animated step indicators for the reasoning trace — numbered steps that glow teal as they activate, connected by a thin animated line
- The cold-start chat should feel like a sleek messaging app in dark mode — dark bubbles with teal accent for the agent, slightly lighter bubbles for the user, typing indicator with pulsing dots
- Mobile-responsive: judges may test on phones
- Loading states should be characterful with a terminal/hacker aesthetic: "The agent dey think..." or "Checking the vibe..." rendered in monospace with a blinking cursor (when Naija mode is on)
- Scrollbar styled to match — thin, dark, with teal thumb
- Page transitions should be smooth fades or slides, not jarring

## TECHNICAL CONSTRAINTS
- Build as a React application (single-page, component-based)
- Use Tailwind CSS for utility classes BUT with custom CSS for the distinctive elements (patterns, animations, radar chart)
- Radar chart: use Recharts or D3 for the 7-dimension spider chart
- All API calls go to FastAPI endpoints:
  - POST /task-a/generate — body: { user_id, item_metadata, naija_vibe_mode }
  - POST /task-b/recommend — body: { user_id, category, mood, context }
  - POST /task-b/cold-start — body: { turn_number, user_response }
- For the design mockup/prototype, use mock data that feels realistic (Nigerian names, Nigerian businesses, Pidgin reviews)
- Dark mode support is a bonus but not required

## MOCK DATA TO USE

### Sample User Persona
- Name: "ChiomaNwankwo92"
- Region: Lagos (VI/Lekki corridor)
- Fingerprint: { generosity: 0.72, verbosity: 0.45, emotional_intensity: 0.81, topic_focus: "food_quality + value", consistency: 0.88, recency_weight: 0.65, naija_slang_index: 0.78 }

### Sample Task A Output
- Item: "Mama Cass Restaurant, Victoria Island"
- Generated Review: "Abeg, if you never chop for Mama Cass, you never start. The jollof rice hit different — proper party jollof vibes. Service was a bit slow sha, but the food make up for am. For VI price, e dey reasonable. I go come back with my squad next weekend. 4 stars because that AC need to work harder!"
- Rating: 4.0
- Confidence: 0.87
- Vibe Score: 0.84

### Sample Task B Recommendations
1. "The Place Restaurant, Lekki" — Match: 94% — "Your jollof rating history says you'll love this one"
2. "Buka Steki, Surulere" — Match: 88% — "Budget-friendly and the portions no be small thing"
3. "Nkoyo, Ikoyi" — Match: 82% — "Step up from your usual — special occasion vibes"

### Sample Evaluation Metrics (for Evaluation page)
- ROUGE-L: 0.42 (vs baseline 0.31 → +35%)
- BERTScore: 0.78 (vs baseline 0.69 → +13%)
- Rating RMSE: 0.61 (vs baseline 0.89 → -31%)
- NDCG@10: 0.74 (vs baseline 0.58 → +28%)
- Avg Naija Vibe Score: 0.81

### Sample Side-by-Side Comparison (for Evaluation page)
**Input:** User "AdekunleRoads" reviewing "Kilimanjaro Restaurant, Wuse II, Abuja"
**Generic Mode Output:** "The restaurant offers a pleasant dining experience with a diverse menu. The service is attentive and the ambiance is nice. I would recommend it for a casual dinner. Rating: 4/5"
**Naija Vibe Mode Output:** "Guy, Kilimanjaro no dey disappoint. The suya platter was fire — proper Abuja standard. Waiter dem sabi their work, no wahala. The only thing be say parking for Wuse II na war, but once you enter, e worth am. If you dey Abuja and you never go here, you dey owe yourself. 4 stars — would be 5 but make dem reduce that pepper small for the coleslaw 😂"

### Team Data
- Testimony: Role — "Agent Architecture & ML Engineering", Quote — "I wanted to build AI that sounds like the people I grew up with.", Color accent — Electric teal (#00D4AA)
- Aaliyah: Role — "Memory Systems & Data Pipeline", Quote — "The data gap isn't a limitation — it's an opportunity to be original.", Color accent — Warm amber (#E8A838)
- Shiloh: Role — "Nigerian Language Module & Cultural Research", Quote — "If the vibe check fails, we don't ship it.", Color accent — Muted lavender (#8B7EC8)

## WHAT MAKES THIS DESIGN WIN

The judges will evaluate 20+ submissions. Most will have bare API endpoints or generic Bootstrap dashboards. This UI should:
1. **Be MEMORABLE** — the storytelling landing page creates an emotional connection before the judge even touches a button. They'll remember the story, not just the tool.
2. **Be USABLE** — a judge can input a persona and get results in under 30 seconds
3. **SHOW the intelligence** — the reasoning trace, fingerprint chart, vibe scores, and evaluation metrics make the agent's sophistication visible and measurable
4. **Feel NIGERIAN** — not "AI tool with green accent color" but genuinely Nigerian in voice, visuals, narrative, and energy
5. **PROVE the thesis** — the side-by-side comparison page is the single most persuasive element. It shows in 3 seconds why culture-first architecture matters.
6. **Be DOWNLOADABLE** — judges can grab the solution paper and supplementary docs without leaving the app
7. **Be RESPONSIVE** — works on desktop and mobile
8. **Tell a STORY** — from "here's the problem" to "here's how we solved it" to "try it yourself" to "here are the results" — the entire site is a narrative arc

Build this as a complete, functional React application with all pages, components, mock data, animations, and scroll-driven storytelling. Make it extraordinary.
```

---

## HOW TO USE THIS PROMPT

1. **Open a new Claude conversation** (or use Claude Artifacts)
2. **Paste the entire prompt above** (everything inside the code block)
3. Claude will generate a full React application with all the pages, components, and styling
4. **Iterate** — ask Claude to refine specific sections, change colors, add animations, etc.
5. Once you're happy with the design, use it as the reference to build your actual frontend

## TIPS FOR ITERATION

After the first generation, you can follow up with prompts like:
- "Make the radar chart more prominent and add a glow effect when Naija Vibe Mode is active"
- "The cold-start chat flow needs typing indicators and smoother transitions"
- "Add a comparison view where users can toggle Naija Vibe Mode on/off and see both review versions side by side"
- "Make the landing page hero section more dramatic with an animated background"
- "Add a dark mode toggle and make the dark theme feel like Lagos nightlife"
- "The team section needs real profile images — here are the URLs: [paste URLs]"
- "Make the solution paper download section feel more premium — like you're downloading a research publication"
- "The 'Why Culture Matters' manifesto section needs more emotional punch — add a pull quote with larger typography"
- "The side-by-side comparison on the Evaluation page should auto-animate the text appearing word by word"
- "The architecture scrollytelling is too fast — slow down the node-by-node animation"
- "Add a loading skeleton that shows while the evaluation metrics are loading"

## PAGE SUMMARY

| # | Page | Purpose | Judge Impact |
|---|------|---------|-------------|
| 1 | Landing (Storytelling) | Hook → Problem → Solution → Culture Manifesto → Team → CTAs | First impression, emotional buy-in |
| 2 | Task A — Review Gen | Interactive demo of user modeling agent | Proves Task A works |
| 3 | Task B — Recommendations | Interactive demo with cold-start chat flow | Proves Task B works + cold-start |
| 4 | How It Works | Animated architecture walkthrough | Shows engineering depth |
| 5 | Solution Paper & Resources | Paper download, supplementary docs, GitHub link | Primary talent signal access |
| 6 | Evaluation Playground | Metrics dashboard + side-by-side comparison | Proves the thesis quantitatively |
