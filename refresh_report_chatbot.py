#!/usr/bin/env python3
"""Strip old chatbot from report HTML files and re-inject with current library.

The report files (lps-caste-dashboard.html, lps-caste-investigation.html) have
an old version of the chatbot baked in with hardcoded cyan colors, old model
lists, and missing features. This script strips the old chatbot CSS/HTML/JS
and re-injects using the current chatbot-in-html library with the newspaper theme.

Usage:
    python refresh_report_chatbot.py
"""

import re
from pathlib import Path

from chatbot_in_html import inject_chatbot
from chatbot_in_html.themes import THEME_NEWSPAPER

REPORTS_DIR = Path(__file__).parent / "docs" / "reports"

REPORTS = {
    "lps-caste-dashboard.html": {
        "assistant_name": "Ask The Record",
        "system_prompt": (
            "You are the reader assistant for The Amaravati Record, embedded in the "
            "Caste Distribution Dashboard. This interactive report analyses 47,993 plots "
            "allocated under the APCRDA Land Pooling Scheme across 26 villages in the "
            "Krishna-Guntur corridor. Key finding: Kamma community holds 57.4% of plots, "
            "followed by Kapu (13.0%) and Reddy (5.0%). Classification uses a 5,548-surname "
            "ground truth corpus + Gemini 2.5 Flash per-name classifier (99.6% rate). "
            "The report has tabs: Overview, Plot Map, Village Breakdown, Data Sources & Process, "
            "Search Raw Data. PII is masked. Answer concisely using markdown. "
            "Do not invent numbers — use only what is in the report data."
        ),
        "welcome_message": "Ask me anything about this report. I can see the section you are currently viewing.",
        "suggestions": [
            "Summarize the caste distribution",
            "Which villages have the most plots?",
            "Explain the methodology",
            "What are the confidence levels?",
        ],
    },
    "lps-caste-investigation.html": {
        "assistant_name": "Ask The Record",
        "system_prompt": (
            "You are the reader assistant for The Amaravati Record, embedded in the "
            "Broadsheet Investigation report. This narrative investigation covers the "
            "finding that 57.4% of 47,993 APCRDA Land Pooling Scheme plots are held by "
            "the Kamma community across 26 villages. The report is written in broadsheet "
            "newspaper format with a lead story, sidebar analysis, pull quotes, and a "
            "dispatch board. Answer concisely using markdown. Do not invent numbers."
        ),
        "welcome_message": "Ask me about this investigation. I can help explain the findings and methodology.",
        "suggestions": [
            "What is the main finding?",
            "How were the names classified?",
            "What is the Kamma percentage?",
            "Where does the data come from?",
        ],
    },
}


def strip_old_chatbot(html: str) -> str:
    """Remove all old chatbot CSS, HTML, and JS blocks from the HTML."""

    # 1. Strip old chatbot CSS blocks (may be multiple <style> blocks)
    # Pattern: <style> containing "Chatbot Styles" or "Chatbot Theme Overrides"
    html = re.sub(
        r'<style>\s*/\*\s*---\s*Chatbot\s*(Styles|Theme Overrides)[^<]*</style>\s*',
        '',
        html,
        flags=re.DOTALL,
    )

    # 2. Strip chatbot HTML elements (bubble + window with all nested children)
    # Match from <!-- Chatbot Bubble --> through the chatbot window's final </div>
    # by counting div nesting depth to find the correct closing tag.
    def strip_chatbot_html(h):
        while True:
            start = h.find('<!-- Chatbot Bubble -->')
            if start == -1:
                # Also try matching by ID directly
                start = h.find('<div id="chatbotBubble"')
                if start == -1:
                    break
            # Find the chatbotWindow div after the bubble
            win_start = h.find('<div id="chatbotWindow"', start)
            if win_start == -1:
                # Just a bubble without window — remove until next -->
                end = h.find('</div>', start)
                if end != -1:
                    h = h[:start] + h[end + 6:]
                break
            # Count nesting to find the window's closing </div>
            depth = 0
            i = win_start
            while i < len(h):
                if h[i:i+4] == '<div':
                    depth += 1
                    i += 4
                elif h[i:i+6] == '</div>':
                    depth -= 1
                    if depth == 0:
                        # Found the matching close
                        h = h[:start] + h[i + 6:]
                        break
                    i += 6
                else:
                    i += 1
            else:
                break  # Safety: couldn't find matching close
        return h
    html = strip_chatbot_html(html)

    # 3. Strip chatbot JS block
    # Pattern: <script> containing chatbot configuration constants
    html = re.sub(
        r'<script>\s*(?://[^\n]*\n)*\s*(?:const CHATBOT_|const GENAI_|const SYSTEM_PROMPT|const WELCOME_MSG).*?</script>',
        '',
        html,
        flags=re.DOTALL,
    )

    # 4. Strip the marked.js loader script tag if present
    html = re.sub(
        r'<script\s+src="https://cdn\.jsdelivr\.net/npm/marked[^"]*"[^>]*></script>\s*',
        '',
        html,
    )

    # Clean up multiple blank lines left behind
    html = re.sub(r'\n{4,}', '\n\n\n', html)

    return html


def refresh_report(filename: str) -> None:
    """Strip old chatbot and re-inject with current library."""
    filepath = REPORTS_DIR / filename
    if not filepath.exists():
        print(f"  SKIP {filename} — not found")
        return

    cfg = REPORTS[filename]
    html = filepath.read_text(encoding="utf-8")

    # Check if old chatbot exists
    old_markers = html.count("#4cc9f0") + html.count("Phi-3.5-mini")
    if old_markers == 0 and "cb-accent" in html and "addSuggestionChips" in html:
        print(f"  SKIP {filename} — already using current chatbot")
        return

    print(f"  Stripping old chatbot from {filename}...")
    html = strip_old_chatbot(html)

    print(f"  Re-injecting with current library + newspaper theme...")
    html = inject_chatbot(
        html,
        assistant_name=cfg["assistant_name"],
        system_prompt=cfg["system_prompt"],
        welcome_message=cfg["welcome_message"],
        suggestions=cfg["suggestions"],
        default_backend="webllm",
        custom_css=THEME_NEWSPAPER,
        storage_prefix="amaravati",
    )

    filepath.write_text(html, encoding="utf-8")
    size_mb = len(html.encode("utf-8")) / 1024 / 1024
    print(f"  DONE {filename} ({size_mb:.1f} MB)")


def main():
    print("Refreshing report chatbots...")
    for filename in REPORTS:
        refresh_report(filename)
    print("Done.")


if __name__ == "__main__":
    main()
