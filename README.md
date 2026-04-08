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

- **Playwright** (for URL capture). The bundled `extract_style.py` uses `uv run` and will install Playwright automatically on first run. You can also skip the URL path entirely and paste HTML/CSS from browser dev tools.
- **Claude Code** or **GitHub Copilot CLI** — both read the `.claude-plugin/` format.

## What's inside

```
.claude-plugin/
├── marketplace.json      marketplace listing
└── plugin.json           plugin manifest
skills/
└── style-guide-extraction/
    ├── SKILL.md          skill instructions
    └── scripts/
        └── extract_style.py   Playwright-based CSS/HTML extractor
```

## License

MIT
