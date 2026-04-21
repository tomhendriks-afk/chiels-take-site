#!/usr/bin/env python3
"""
publish.py — publish a new Chiel's Take article.

Usage:
  python3 publish.py drafts/my-new-take.md

What it does:
  1. Parses the markdown draft (YAML-ish frontmatter + body).
  2. Converts the body to HTML.
  3. Renders the article page from _template.html.
  4. Updates articles.json (inserts or updates by slug, sorts by date desc).
  5. Regenerates index.html with the 3-card leaderboard rotation.

What it does NOT do:
  - Touch git. Review with `git diff`, then commit and push yourself.
  - Push images. If your draft references images, copy them into the repo manually.

Consistent with the Ambient Advantage architecture approach:
  - Python (matches the cloud-run-podcast pipeline).
  - Stdlib-only, no external dependencies.
  - Idempotent — running twice on the same draft is safe.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()
ARTICLE_TEMPLATE = REPO_ROOT / "_template.html"
INDEX_TEMPLATE = REPO_ROOT / "_index_template.html"
ARTICLES_JSON = REPO_ROOT / "articles.json"
INDEX_PATH = REPO_ROOT / "index.html"


# ---------- frontmatter + markdown parsing ----------

def parse_draft(text: str) -> tuple[dict, str]:
    """Split a draft into (frontmatter_dict, body_markdown)."""
    if not text.lstrip().startswith("---"):
        raise ValueError(
            "Draft must start with a '---' frontmatter block. "
            "See drafts/EXAMPLE.md for the expected format."
        )
    # Find the closing --- line
    lines = text.lstrip().splitlines()
    # lines[0] is the opening ---
    close_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close_idx = i
            break
    if close_idx is None:
        raise ValueError("Frontmatter block is not closed with a trailing '---'.")

    fm_lines = lines[1:close_idx]
    body = "\n".join(lines[close_idx + 1:]).strip()

    meta: dict = {}
    for raw in fm_lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if ":" not in raw:
            raise ValueError(f"Bad frontmatter line (missing ':'): {raw!r}")
        key, _, value = raw.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"-+", "-", value)
    return value


def inline_format(s: str) -> str:
    """Handle **bold**, *italic*, [link](url) in a single line of text."""
    # Bold FIRST so we don't double-eat asterisks
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def markdown_to_html(md: str) -> str:
    """Minimal markdown → HTML matching the existing .article-body style.
    Supports: paragraphs, ## H2 headings, *italic*, **bold**, [links](url).
    Lists, code blocks, images etc. are NOT supported — add them here if needed.
    """
    md = md.replace("\r\n", "\n").strip()
    blocks = re.split(r"\n\s*\n", md)
    out = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            heading = inline_format(block[3:].strip())
            out.append(f"    <h2>{heading}</h2>")
        elif block.startswith("# "):
            # Skip an H1 — the title is rendered separately from frontmatter
            continue
        else:
            paragraph = re.sub(r"\s*\n\s*", " ", block)
            paragraph = inline_format(paragraph)
            out.append(f"    <p>{paragraph}</p>")
    return "\n\n".join(out)


# ---------- metadata derivation ----------

def format_display_date(iso_date: str) -> str:
    """'2026-04-22' → 'April 22, 2026'."""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    # %-d works on macOS/Linux; fall back for other platforms
    try:
        return dt.strftime("%B %-d, %Y")
    except ValueError:
        return dt.strftime("%B %d, %Y").replace(" 0", " ")


def estimate_read_time(body_md: str) -> str:
    words = len(re.findall(r"\w+", body_md))
    minutes = max(1, round(words / 200))
    return str(minutes)


def first_paragraph_excerpt(body_md: str, max_words: int = 42) -> str:
    first = re.split(r"\n\s*\n", body_md.strip())[0]
    # Strip markdown
    first = re.sub(r"\*\*(.+?)\*\*", r"\1", first)
    first = re.sub(r"\*(.+?)\*", r"\1", first)
    first = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", first)
    first = re.sub(r"^#+\s*", "", first, flags=re.MULTILINE)
    first = re.sub(r"\s+", " ", first).strip()
    words = first.split()
    if len(words) <= max_words:
        return first
    return " ".join(words[:max_words]).rstrip(",.;:") + "..."


def enrich_meta(meta: dict, body_md: str) -> dict:
    """Fill in derivable fields; validate required ones."""
    if "title" not in meta or not meta["title"]:
        raise ValueError("Frontmatter must include 'title'.")

    meta.setdefault("tag", "Opinion")
    meta.setdefault("slug", slugify(meta["title"]))
    meta.setdefault("date", datetime.today().strftime("%Y-%m-%d"))
    meta.setdefault("read_time", estimate_read_time(body_md))
    meta.setdefault("excerpt", first_paragraph_excerpt(body_md))

    # Normalize date
    try:
        datetime.strptime(meta["date"], "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Frontmatter 'date' must be YYYY-MM-DD, got {meta['date']!r}")

    meta["date_display"] = format_display_date(meta["date"])
    meta["read_time_display"] = f"{meta['read_time']} min read"
    return meta


# ---------- rendering ----------

def render_article(meta: dict, body_html: str) -> str:
    template = ARTICLE_TEMPLATE.read_text()
    replacements = {
        "{{TITLE}}": meta["title"],
        "{{META_DESCRIPTION}}": meta["excerpt"],
        "{{OG_DESCRIPTION}}": meta["excerpt"],
        "{{TAG}}": meta["tag"],
        "{{READ_TIME}}": meta["read_time"],
        "{{DATE_DISPLAY}}": meta["date_display"],
        "{{ARTICLE_BODY}}": body_html,
    }
    for k, v in replacements.items():
        template = template.replace(k, v)
    return template


def render_latest_card(a: dict) -> str:
    return f'''  <!-- CARD 1 — Latest (with author sidebar) -->
  <article class="lb-card is-latest">
    <div>
      <div class="lb-label">
        <span class="lb-label-dot"></span>
        Latest Take
      </div>
      <span class="lb-tag">{a["tag"]}</span>
      <h2 class="lb-headline"><a href="{a["slug"]}.html">{a["title"]}</a></h2>
      <p class="lb-excerpt">{a["excerpt"]}</p>
      <div class="lb-meta">
        <span class="author">Chiel Hendriks</span>
        <span>&middot;</span>
        <span>{a["read_time"]}</span>
        <span>&middot;</span>
        <span>{a["date_display"]}</span>
      </div>
      <a href="{a["slug"]}.html" class="lb-read-btn">Read the full take &rarr;</a>
    </div>
    <aside class="lb-author">
      <div class="lb-author-avatar"><img src="chiel.jpg" alt="Chiel Hendriks"></div>
      <div class="lb-author-name">Chiel Hendriks</div>
      <div class="lb-author-title">Managing Director, PwC Canada<br>Ex-Google &middot; 16 years</div>
      <p class="lb-author-bio">Where the daily briefing tells you what happened in AI, this column tells you what it means — and what to do about it.</p>
    </aside>
  </article>'''


def render_leaderboard_card(a: dict) -> str:
    return f'''  <!-- Leaderboard card -->
  <article class="lb-card">
    <div class="lb-label muted"><span class="lb-label-dot"></span>Recent</div>
    <span class="lb-tag">{a["tag"]}</span>
    <h2 class="lb-headline"><a href="{a["slug"]}.html">{a["title"]}</a></h2>
    <p class="lb-excerpt">{a["excerpt"]}</p>
    <div class="lb-meta">
      <span class="author">Chiel Hendriks</span>
      <span>&middot;</span>
      <span>{a["read_time"]}</span>
      <span>&middot;</span>
      <span>{a["date_display"]}</span>
    </div>
    <a href="{a["slug"]}.html" class="lb-read-btn">Read the full take &rarr;</a>
  </article>'''


def render_prev_card(a: dict) -> str:
    return f'''    <div class="take-card">
      <span class="take-tag">{a["tag"]}</span>
      <div class="take-date">{a["date_display"]}</div>
      <h3><a href="{a["slug"]}.html">{a["title"]}</a></h3>
      <p class="take-excerpt">{a["excerpt"]}</p>
      <a href="{a["slug"]}.html" class="take-read">Read &rarr;</a>
    </div>'''


def _normalize_article_entry(a: dict) -> dict:
    """Ensure each article dict has the fields the card renderers need.
    Handles the historical 'X min read' vs bare number for read_time.
    """
    out = dict(a)
    rt = str(out.get("read_time", "")).strip()
    if not rt.endswith("read"):
        # Plain number → '5 min read'
        out["read_time"] = f"{rt} min read"
    return out


def render_index(articles: list) -> str:
    template = INDEX_TEMPLATE.read_text()
    articles = [_normalize_article_entry(a) for a in articles]

    stack = articles[:3]
    prev = articles[3:]

    stack_parts = []
    for i, a in enumerate(stack):
        if i == 0:
            stack_parts.append(render_latest_card(a))
        else:
            stack_parts.append(render_leaderboard_card(a))
    featured_html = "\n\n".join(stack_parts)

    if prev:
        prev_cards = "\n".join(render_prev_card(a) for a in prev)
        prev_html = f'''
<!-- PREVIOUS TAKES — graduated from leaderboard -->
<div class="prev-section">
  <div class="prev-section-header">
    <h2>Previous Takes</h2>
  </div>
  <div class="takes-grid">
{prev_cards}
  </div>
</div>
'''
    else:
        prev_html = ""

    return template.replace("{{FEATURED_STACK}}", featured_html).replace("{{PREV_SECTION}}", prev_html)


# ---------- articles.json bookkeeping ----------

def update_articles_json(meta: dict) -> list:
    articles = []
    if ARTICLES_JSON.exists():
        articles = json.loads(ARTICLES_JSON.read_text())

    # Remove existing entry with same slug (so re-running on an updated draft overwrites)
    articles = [a for a in articles if a.get("slug") != meta["slug"]]

    articles.append({
        "slug": meta["slug"],
        "title": meta["title"],
        "tag": meta["tag"],
        "date": meta["date"],
        "date_display": meta["date_display"],
        "read_time": meta["read_time_display"],
        "excerpt": meta["excerpt"],
        "featured": False,
    })
    # Sort newest first
    articles.sort(key=lambda a: a["date"], reverse=True)
    # Mark newest as featured
    for i, a in enumerate(articles):
        a["featured"] = (i == 0)

    ARTICLES_JSON.write_text(json.dumps(articles, indent=2) + "\n")
    return articles


# ---------- main ----------

def publish(draft_path: Path) -> None:
    if not draft_path.exists():
        raise SystemExit(f"Draft not found: {draft_path}")

    raw = draft_path.read_text()
    meta, body_md = parse_draft(raw)
    meta = enrich_meta(meta, body_md)

    print(f"Publishing: {meta['title']}")
    print(f"  slug:      {meta['slug']}")
    print(f"  date:      {meta['date_display']}")
    print(f"  read time: {meta['read_time']} min")
    print(f"  excerpt:   {meta['excerpt'][:80]}{'...' if len(meta['excerpt']) > 80 else ''}")

    # 1. Render article HTML
    body_html = markdown_to_html(body_md)
    article_html = render_article(meta, body_html)
    article_out = REPO_ROOT / f"{meta['slug']}.html"
    article_out.write_text(article_html)
    print(f"  wrote:     {article_out.relative_to(REPO_ROOT)}")

    # 2. Update articles.json
    articles = update_articles_json(meta)
    print(f"  updated:   articles.json ({len(articles)} total)")

    # 3. Regenerate index.html
    index_html = render_index(articles)
    INDEX_PATH.write_text(index_html)
    stack_count = min(3, len(articles))
    prev_count = max(0, len(articles) - 3)
    print(f"  rebuilt:   index.html — {stack_count} in leaderboard, {prev_count} in Previous Takes")

    print()
    print("Done. Next steps:")
    print("  git diff               # review what changed")
    print("  git add .              # stage")
    print("  git commit -m '…'      # commit")
    print("  git push origin main   # push; Cloudflare auto-deploys")


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    publish(Path(sys.argv[1]).expanduser().resolve())


if __name__ == "__main__":
    main()
