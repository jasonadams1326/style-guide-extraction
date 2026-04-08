# Style Guide Extraction

Turn any website's visual style into a reusable design system. Works with both **Claude Code** and **GitHub Copilot CLI**.

Three phases, invoked as subcommands:

- `/sge design <url>` — Capture a reference page and recreate it as `design.html`
- `/sge styleguide` — Distill `design.html` into a detailed `styleguide.md`
- `/sge build <description>` — Build new UI in the captured style

## Why

Screenshots alone give AI agents ~60–70% style fidelity. The missing details — exact colors, font weights, spacing tokens, subtle shadows — live in the CSS. This skill extracts them via Playwright, then iterates with you on a pixel-faithful `design.html`, and finally distills that into a portable style guide you (or an agent) can build against.

## Install

### Claude Code

```bash
claude plugin marketplace add github:jasonadams1326/style-guide-extraction
claude plugin install style-guide-extraction
```

### GitHub Copilot CLI

```bash
copilot plugin install jasonadams1326/style-guide-extraction
```

## Usage

After install, in either CLI:

```
/sge design https://linear.app
```

The agent will capture the page, build a `design.html`, and ask you to review side-by-side with the original. Once you approve it:

```
/sge styleguide
```

Generates a `styleguide.md` you can carry into any project. Then:

```
/sge build a pricing page with three tiers
```

Produces a new `output.html` that faithfully follows the captured style.

## Requirements

**Required:** Claude Code or GitHub Copilot CLI — both read the `.claude-plugin/` format.

**Recommended (for URL capture):** [Playwright MCP](https://github.com/microsoft/playwright-mcp) installed as an MCP server in your CLI. This is how the skill captures a page end-to-end: the agent opens a headed browser, you can log in if the site is auth-gated, and it extracts real rendered HTML, CSS, computed styles, and a full-page screenshot. It's also the only path that reliably handles JavaScript-rendered pages, animations, and hover states.

**Fallback:** paste HTML/CSS from your browser dev tools (right-click → Inspect → Copy outer HTML, plus the relevant stylesheets). Works on any page with no install required, but you lose runtime details like animations and computed values.

You don't need Python, Node, `uv`, or anything else.

## What's inside

```
.claude-plugin/
├── marketplace.json      marketplace listing
└── plugin.json           plugin manifest
skills/
└── style-guide-extraction/
    └── SKILL.md          skill instructions (pure prompt — no code)
```

## License

MIT
