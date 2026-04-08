#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "playwright>=1.40.0",
# ]
# ///
"""
Extract style reference material from a URL using Playwright.
Mimics what a human does in browser dev tools: copy outer HTML, copy CSS,
take a screenshot.

Outputs to <output-dir>:
- reference.html      post-JS outer HTML of <html>
- reference.css       concatenated raw CSS (stylesheets + inline <style>)
- reference.png       full-page screenshot
- computed.json       computed styles for common selectors
- meta.json           {final_url, title, viewport}

Usage:
    uv run extract_style.py <url> [--output-dir DIR] [--auth] [--headless]

Auth flow (for sites requiring login):
    Run with --auth and the agent should invoke this with run_in_background.
    The script will:
      1. Launch headful browser, navigate to URL
      2. Create <output-dir>/.sge-waiting sentinel
      3. Poll for <output-dir>/.sge-ready sentinel
      4. When ready sentinel appears, extract from CURRENT page (user may
         have navigated after login) and exit
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright, Response


KEY_SELECTORS = [
    "body", "h1", "h2", "h3", "h4", "h5", "p", "a", "button",
    "header", "nav", "main", "footer", "section", "article", "aside",
    "input", "label", "ul", "li",
    ".btn", ".button", ".card", ".hero", ".container", ".wrapper",
]

COMPUTED_PROPERTIES = [
    "color", "backgroundColor", "fontFamily", "fontSize", "fontWeight",
    "lineHeight", "letterSpacing", "padding", "margin",
    "borderRadius", "borderColor", "borderWidth", "borderStyle",
    "boxShadow", "textTransform",
]


async def extract(url: str, output_dir: Path, auth: bool, headless: bool, timeout: int):
    output_dir.mkdir(parents=True, exist_ok=True)
    waiting_file = output_dir / ".sge-waiting"
    ready_file = output_dir / ".sge-ready"

    for f in (waiting_file, ready_file):
        if f.exists():
            f.unlink()

    css_files: dict[str, str] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await context.new_page()

        async def handle_response(response: Response):
            try:
                if response.request.resource_type == "stylesheet":
                    body = await response.text()
                    css_files[response.url] = body
            except Exception:
                pass

        page.on("response", handle_response)

        print(f"[sge] Navigating to {url}", file=sys.stderr)
        try:
            await page.goto(url, wait_until="networkidle", timeout=60_000)
        except Exception as e:
            print(f"[sge] networkidle wait timed out, continuing: {e}", file=sys.stderr)

        # Disable CSS animations/transitions so content that animates in is visible in the screenshot
        await page.evaluate("""() => {
            const style = document.createElement('style');
            style.textContent = `
                *, *::before, *::after {
                    animation-duration: 0.001ms !important;
                    animation-delay: 0ms !important;
                    transition-duration: 0.001ms !important;
                    transition-delay: 0ms !important;
                }
            `;
            document.head.appendChild(style);
        }""")

        # Scroll through the entire page to trigger lazy loading / intersection observers
        page_height = await page.evaluate("() => document.body.scrollHeight")
        step = 800
        pos = 0
        while pos < page_height:
            await page.evaluate(f"() => window.scrollTo(0, {pos})")
            await asyncio.sleep(0.05)
            pos += step
        await page.evaluate("() => window.scrollTo(0, 0)")
        # Brief wait for any triggered lazy loads to settle
        await asyncio.sleep(1)

        if auth:
            waiting_file.write_text(json.dumps({
                "initial_url": url,
                "current_url": page.url,
            }))
            print(f"[sge] WAITING for ready signal", file=sys.stderr)
            print(f"[sge] To proceed: touch {ready_file}", file=sys.stderr)
            print(f"[sge] Current URL: {page.url}", file=sys.stderr)
            deadline = time.time() + timeout
            while not ready_file.exists():
                if time.time() > deadline:
                    print(f"[sge] Timeout after {timeout}s", file=sys.stderr)
                    await browser.close()
                    sys.exit(2)
                await asyncio.sleep(1)
            ready_file.unlink()
            if waiting_file.exists():
                waiting_file.unlink()
            try:
                await page.wait_for_load_state("networkidle", timeout=30_000)
            except Exception:
                pass

        final_url = page.url
        title = await page.title()
        print(f"[sge] Extracting from {final_url}", file=sys.stderr)

        html = await page.evaluate("() => document.documentElement.outerHTML")
        (output_dir / "reference.html").write_text(html)

        inline_styles = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('style'))
                .map(s => s.textContent || '')
                .join('\\n\\n');
        }""")

        css_chunks = []
        if inline_styles.strip():
            css_chunks.append(f"/* === inline <style> blocks === */\n{inline_styles}")
        for src, body in css_files.items():
            css_chunks.append(f"/* === {src} === */\n{body}")
        (output_dir / "reference.css").write_text("\n\n".join(css_chunks))

        computed = await page.evaluate(
            """(args) => {
                const [selectors, props] = args;
                const results = {};
                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    if (!els.length) continue;
                    const el = els[0];
                    const cs = window.getComputedStyle(el);
                    const obj = { _count: els.length };
                    for (const p of props) obj[p] = cs[p];
                    results[sel] = obj;
                }
                return results;
            }""",
            [KEY_SELECTORS, COMPUTED_PROPERTIES],
        )
        (output_dir / "computed.json").write_text(json.dumps(computed, indent=2))

        await page.screenshot(path=str(output_dir / "reference.png"), full_page=True)

        meta = {
            "final_url": final_url,
            "initial_url": url,
            "title": title,
            "viewport": {"width": 1440, "height": 900},
            "stylesheets_captured": len(css_files),
        }
        (output_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        print(f"[sge] Done", file=sys.stderr)
        # final stdout line is JSON for the agent to parse
        print(json.dumps({
            "status": "ok",
            "final_url": final_url,
            "title": title,
            "output_dir": str(output_dir),
            "files": ["reference.html", "reference.css", "reference.png", "computed.json", "meta.json"],
        }))

        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="Extract style reference from a URL")
    parser.add_argument("url", help="URL to extract from")
    parser.add_argument("--output-dir", default="./sge-capture", help="Where to write outputs")
    parser.add_argument("--auth", action="store_true", help="Wait for ready sentinel before extracting (HITL auth)")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (no UI)")
    parser.add_argument("--timeout", type=int, default=600, help="Max seconds to wait in --auth mode")
    args = parser.parse_args()

    asyncio.run(extract(
        url=args.url,
        output_dir=Path(args.output_dir),
        auth=args.auth,
        headless=args.headless,
        timeout=args.timeout,
    ))


if __name__ == "__main__":
    main()
