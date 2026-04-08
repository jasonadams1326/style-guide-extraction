---
name: style-guide-extraction
description: |
  Extract, clone, copy, or replicate a website's visual style into a reusable design
  system. Three phases: capture a reference page (URL via Playwright OR pasted
  HTML/CSS) and recreate it as a pixel-perfect design.html, generate a styleguide.md,
  then build new UI in that style. Use when the user wants to clone/copy/rip/mimic a
  site's look, make a style guide, build "like Stripe/Linear/Vercel", or pastes raw
  HTML/CSS from dev tools.
user-invocable: true
---

# Style Guide Extraction

Turn any website's visual style into a reusable design system. Three phases — each is a separate subcommand so you can enter the pipeline wherever makes sense.

**Why this pipeline exists:** Screenshots alone give AI agents ~60-70% style fidelity. The missing details (exact colors, font weights, spacing tokens, subtle shadows) live in the CSS. By combining real CSS extraction with iterative human review, you build a reference implementation that captures 100% of the style — then distill it into a portable guide.

## Subcommands

- `/sge design [url]` — Capture a reference page and recreate it as `design.html`
- `/sge styleguide` — Generate a detailed style guide from the finished `design.html`
- `/sge build [description]` — Build new UI using the style guide

If called without a subcommand (`/sge`), briefly explain the three phases and ask the user which step they're on.

---

## Phase 1: Design (`/sge design`)

**Goal:** Produce a single `design.html` file that faithfully recreates the user's reference website style. This becomes the source of truth for everything that follows.

There are two paths into this phase. **Default to the URL path** unless the user has already pasted HTML/CSS or explicitly says they want to paste it themselves.

### Path A: URL → subagent via Playwright MCP (default)

Spawn a **general-purpose subagent** to handle all the browser work. This keeps the raw HTML/CSS noise out of the main conversation context — the subagent digests it and hands back only a compact design brief.

#### What to tell the subagent

Give it a prompt like this (adapt as needed):

```
You have access to Playwright MCP browser tools. Your job is to extract the
visual design from <URL> and save the results to ./sge-capture/, then return
a compact design brief.

Steps:
1. Navigate to <URL>
2. Check if the page requires auth (login form, redirect to /login, blank/empty
   content, etc.). If yes, stop and return {"needs_auth": true, "current_url": "..."}.
3. Disable CSS animations by evaluating this JS:
     const s = document.createElement('style');
     s.textContent = '*,*::before,*::after{animation-duration:0.001ms!important;transition-duration:0.001ms!important}';
     document.head.appendChild(s);
4. Scroll through the full page (scroll to bottom in steps, then back to top)
   to trigger lazy loading and intersection observers. Wait ~1s after scrolling.
5. Take a full-page screenshot → save to ./sge-capture/reference.png
6. Extract outer HTML (post-JS): document.documentElement.outerHTML
   → save to ./sge-capture/reference.html
7. Extract all CSS — inline <style> blocks + text of all loaded stylesheets:
   Array.from(document.styleSheets).map(s => {
     try { return '/* '+s.href+' */\n'+Array.from(s.cssRules).map(r=>r.cssText).join('\n') }
     catch(e) { return '/* blocked: '+s.href+' */' }
   }).join('\n\n')
   Plus: Array.from(document.querySelectorAll('style')).map(s=>s.textContent).join('\n\n')
   Combine and save to ./sge-capture/reference.css
8. Get computed styles for: body, h1, h2, h3, h4, p, a, button, nav, header,
   footer, section, input — for each selector capture: color, backgroundColor,
   fontFamily, fontSize, fontWeight, lineHeight, letterSpacing, padding, margin,
   borderRadius, boxShadow
   Save as JSON to ./sge-capture/computed.json
9. Save {"final_url": page.url, "title": document.title} to ./sge-capture/meta.json

Then analyze everything and return ONLY this compact design brief (not the raw files):
{
  "final_url": "...",
  "title": "...",
  "theme": "dark" or "light",
  "fonts": {"primary": "...", "mono": "..." (if any)},
  "colors": {
    "background": "#...",
    "surface": "#... (card/panel bg if different)",
    "text": "#...",
    "text_muted": "#... (secondary/dimmed text)",
    "accent": "#... (primary CTA/brand color)",
    "border": "#..."
  },
  "type_scale": [
    {"selector": "h1", "size": "68px", "weight": "400", "tracking": "-1.7px", "color": "..."},
    ... (h2, h3, p, nav, button)
  ],
  "spacing": {
    "section_padding": "...",
    "card_padding": "...",
    "button_padding": "..."
  },
  "border_radius": {"button": "...", "card": "..."},
  "shadows": ["..."],
  "page_sections": ["nav", "hero", "features", ...],
  "key_headings": ["exact text of h1", "exact text of h2s..."]
}
```

#### Auth HITL (if subagent returns `needs_auth: true`)

The Playwright MCP browser runs **headed by default** — the user can see it on their screen.

1. Tell the user: "Browser is open at `<current_url>`. Log in and navigate to the exact page you want to capture, then reply 'ready'."
2. When they reply, spawn a new subagent with the same prompt above (Step 1), but note "the user has authenticated in the persistent browser profile — just navigate to `<URL>` and extract."
3. Auth state persists via the profile at `~/.claude/playwright-profile`.

#### What you get back

The subagent returns the compact design brief (not raw HTML/CSS). The raw files are saved in `./sge-capture/` if you need to verify anything. Use the Read tool to view `./sge-capture/reference.png` as a visual reference.

### Path B: User pastes HTML/CSS + screenshot (fallback)

If the user has already extracted HTML/CSS from dev tools themselves, or wants to paste them, use those directly. They might also paste specific CSS values from tools like VisBug ("the bg should be #1a1f36") — apply those literally.

If they only gave a screenshot and no HTML/CSS, ask for one of:
- A URL you can capture via Path A
- The HTML/CSS pasted from dev tools (right-click → Inspect → select `<html>` → Copy outer HTML)

Explain briefly that without the HTML/CSS or a URL, you'll be guessing colors, fonts, and spacing from a screenshot — which gives ~70% fidelity.

### Building `design.html`

With reference material in hand (from either path):

1. **Create `design.html`** in the current working directory. It must be a single self-contained HTML file. Apply the **Design Principles** at the bottom of this skill — they govern all HTML you write, in this phase and Phase 3.

2. **Match what you see, not what's declared.** The CSS file may contain hundreds of unused rules. Use `computed.json` (real browser-rendered values) and the screenshot as the source of truth for what's actually visible. The raw CSS is supporting evidence, not gospel.

3. **Preserve every detail you can.** Colors must match exactly. Fonts must match exactly (including weight — see the "shift one weight thinner" rule in the principles). Spacing, radii, shadows, borders — match them all.

### Phase 1 review gate (HITL — required)

This phase **does not end** until the user explicitly approves the result. Phase 2 depends on `design.html` being a faithful reference, so don't move on prematurely.

After creating `design.html`:

1. Tell the user: "Open `design.html` in your browser side-by-side with the original. How does it look? Tell me what to fix — colors, fonts, spacing, anything."
2. When they point out differences, fix them. They may paste specific values from VisBug or dev tools — use those literally.
3. Iterate until the user says something clearly affirmative ("looks good", "perfect", "ready for the styleguide step", etc.).
4. **Only then** suggest moving to `/sge styleguide`. Do not auto-advance.

### Output
- File: `design.html` in the current working directory
- (And `./sge-capture/` containing the raw extraction artifacts, if Path A was used)

---

## Phase 2: Style Guide (`/sge styleguide`)

**Goal:** Analyze the finished `design.html` and extract a comprehensive, reusable style guide.

### Prerequisites
- A `design.html` file exists in the working directory that the user has approved

If `./sge-capture/` also exists (from Phase 1 Path A), use `reference.css` and `computed.json` as additional evidence for verifying what's actually used.

### Process

1. **Read the source thoroughly** — Parse `design.html` (HTML structure, all inline styles, `<style>` blocks, Tailwind classes). If `./sge-capture/` exists, also read `reference.css` and `computed.json` for ground truth.

2. **Verify before documenting.** This is critical: for every color, font, spacing value, or pattern you document, verify it's actually used prominently. Stylesheets often contain rules that are defined but never applied, or only used in trivial/invisible ways. Cross-reference against `computed.json` if available — those are the real browser-rendered values. The style guide should reflect what's *visually present*, not what's merely declared.

3. **Write `styleguide.md`** with these sections:

   **Overview** — Brief description of the overall aesthetic (dark/light, minimal/rich, corporate/playful, etc.)

   **Color Palette** — Every color actually used, with hex values. Group by role: primary, secondary, accent, background, surface, text, border, etc. Note which colors are dominant vs. supporting.

   **Typography** — Font families, weights, and sizes for each text role (h1-h6, body, caption, button, nav, etc.). Pay special attention to how different fonts pair together. Note line heights and letter spacing where they deviate from defaults.

   **Spacing System** — Document the spacing scale used (is it 4px-based? 8px? Tailwind default?). Show common padding/margin patterns for sections, cards, buttons, etc.

   **Component Styles** — For each distinct component (buttons, cards, nav, inputs, badges, etc.): dimensions, colors, borders, padding, hover states, and any variants.

   **Shadows & Elevation** — All box-shadow values used, mapped to elevation levels (subtle, medium, high). Note where each level appears.

   **Animations & Transitions** — Any transitions on hover, focus, or load. Duration, easing, and which properties animate.

   **Border Radius** — The radius scale in use. Which elements get which radius (buttons vs. cards vs. avatars).

   **Opacity & Transparency** — Any use of opacity, rgba, or backdrop-blur. Where and why.

   **Tailwind CSS Patterns** — If the design uses Tailwind, document the most common utility patterns (e.g., "cards use `rounded-xl shadow-lg p-6 bg-white`").

   **Example Component Code** — Include 2-3 reference HTML snippets showing key components (a button, a card, a section) with the exact styles applied. These serve as copy-paste starting points.

### Output
- File: `styleguide.md` in the current working directory

---

## Phase 3: Build (`/sge build [description]`)

**Goal:** Generate new UI pages or components that faithfully follow the extracted style guide.

### Prerequisites
- A `styleguide.md` file exists in the working directory

### Process

1. **Read `styleguide.md`** in full. Also glance at `design.html` if it exists, as a visual reference.
2. **Understand the request.** The user's description (passed as arguments or in conversation) tells you what to build — could be a dashboard, landing page, settings panel, slide deck, anything.
3. **Generate a single self-contained HTML file** following the style guide and the **Design Principles** below.
4. Save as `output.html` by default, or whatever filename the user specifies.

---

## Design Principles (apply to all HTML output in this skill)

These principles produce high-fidelity, production-quality HTML. They apply to **both** Phase 1 (recreating `design.html`) and Phase 3 (building from the style guide).

### Response shape
- Start with a brief sentence describing what you're building, then the code, then a brief sentence about what to look at or try
- Don't mention tokens, Tailwind, or HTML by name in your prose to the user — just describe what the UI does

### Structure & framework
- Single self-contained HTML file with `<html>`, `<head>`, and `<body>` tags
- Use HTML + Tailwind CSS via CDN. Apply Tailwind utilities directly on elements in the body — avoid setting Tailwind config or defining custom CSS classes
- When custom styles are needed beyond Tailwind, put them in the `style` attribute on the element
- No Tailwind classes on the `<html>` tag — put them on `<body>` or inner elements
- Make it responsive

### Respecting the source design
- **If reference design, code, or HTML is provided (Phase 1, or Phase 3 with a style guide): respect the original design, fonts, colors, and style as much as possible.** This is the most important rule for Phase 1.
- **If no style is specified by the user (Phase 3, no style guide):** design in the spirit of Linear, Stripe, Vercel, or Tailwind UI — but never name them in your output.

### Typography
- Be extremely precise with fonts — they make or break the style match
- For font weight, shift one level thinner than you'd expect (Bold → Semibold, Semibold → Medium). Browser rendering is heavier than design tools, so this compensates.
- Titles above 20px should use `tracking-tight`
- Match font pairings from the reference exactly

### Icons
- Use Lucide icons via CDN (`<script src="https://unpkg.com/lucide@latest"></script>`)
- Always `stroke-width="1.5"` — thinner strokes look more refined
- Avoid wrapping icons in gradient containers

### Interactive elements
- Checkboxes, sliders, dropdowns, and toggles should be custom-styled — never browser defaults. But don't add them gratuitously; only include if the UI calls for them.
- Add hover states: subtle color shifts, outline changes, gentle scale transforms
- Use Tailwind for animations (`transition`, `hover:`, `group-hover:`) — never JavaScript-driven animations

### Visual refinement
- Add subtle dividers and outlines between sections where appropriate
- Use subtle contrast — avoid harsh color jumps
- For logos, use letters with tight tracking, not image placeholders
- If images are needed and none specified, use Unsplash (`https://images.unsplash.com/photo-{id}?w=600`) — faces, 3D renders, abstract, landscapes

### Charts
- Use Chart.js via CDN if charts are needed
- Important canvas bug: never place `<canvas>` as a direct sibling of other block elements at the same level. Wrap it in a `<div>`. Direct sibling placement causes infinite canvas growth. Bad: `<h2><p><canvas><div>`. Good: `<h2><p><div><canvas></div><div>`.

### Theme defaults (Phase 3 only, when style guide is silent)
- Tech / cool / futuristic / developer-focused → dark mode
- Modern / traditional / professional / business → light mode
- If the style guide already specifies a theme, follow it

### What to avoid
- No floating "DOWNLOAD" button in the bottom-right corner
- No mentioning "Tailwind", "HTML", or token counts in your conversational response
- No JavaScript animation libraries
