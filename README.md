# Chiel's Take — publishing workflow

Static site for [take.ambient-advantage.ai](https://take.ambient-advantage.ai).
This README covers the publishing workflow. The site is deployed by Cloudflare
Pages watching the `main` branch of this repo — commits auto-deploy within a
minute or two.

## Publishing a new take

You write the article once as markdown. A script does the rest: renders the
article HTML, updates `articles.json`, and regenerates `index.html` so the
newest three takes sit in the leaderboard and older ones graduate to
"Previous Takes".

### 1. Create a draft

Copy the example to start a new file:

```bash
cp drafts/EXAMPLE.md drafts/my-new-take.md
```

Edit the frontmatter and body. Only `title` is required — everything else has
a sensible default.

```markdown
---
title: The Prompting Premium
tag: Opinion
date: 2026-04-22
read_time: 5
excerpt: A one-sentence hook shown on homepage cards and in link previews.
---

Body here. Plain markdown — paragraphs (blank line between), `## Headings`,
`*italic*`, `**bold**`, `[links](https://example.com)`.
```

### 2. Run the publisher

```bash
python3 publish.py drafts/my-new-take.md
```

It prints what it did. You'll see something like:

```
Publishing: The Prompting Premium
  slug:      the-prompting-premium
  date:      April 22, 2026
  read time: 5 min
  wrote:     the-prompting-premium.html
  updated:   articles.json (3 total)
  rebuilt:   index.html — 3 in leaderboard, 0 in Previous Takes
```

### 3. Review, commit, push

```bash
git diff                                      # sanity-check the changes
git add .                                     # stage everything
git commit -m "Publish: The Prompting Premium"
git push origin main
```

**Always fetch + rebase before pushing** — the Ambient Advantage architecture
has multiple machines that can push to these repos, so pull first to avoid
rejected pushes:

```bash
git fetch origin main && git rebase origin/main
git push origin main
```

Cloudflare Pages picks up the push automatically. Hard-refresh
`take.ambient-advantage.ai` (Cmd+Shift+R) a minute later to see it live.

## How the homepage layout works

- **Card 1 (Latest Take)** — full hero with author sidebar showing `chiel.jpg`.
  Pulsing orange "Latest Take" label.
- **Cards 2 & 3 (Recent)** — same styling, no author sidebar, muted "Recent"
  label. Keeps the hierarchy clear without repeating your face three times.
- **Previous Takes grid** — anything from position 4 onwards. Only appears
  when there are 4+ published articles.

Sort order is by the `date` frontmatter field, newest first. If you publish
out of order, just set the right date and the stack re-orders itself on the
next run.

## Frontmatter fields

| Field       | Required | Default                            | Notes                                                         |
| ----------- | -------- | ---------------------------------- | ------------------------------------------------------------- |
| `title`     | ✓        | —                                  | The headline. Used for `<title>`, H1, and homepage card link. |
| `tag`       |          | `Opinion`                          | Small pill. Use e.g. `Analysis`, `Strategy`, `Field Notes`.   |
| `slug`      |          | Slugified title                    | URL filename. `{slug}.html`. Change with care after publishing — it changes the URL. |
| `date`      |          | Today                              | `YYYY-MM-DD`. Controls homepage sort order.                  |
| `read_time` |          | Estimated from word count (200wpm) | Bare number. Rendered as `{N} min read`.                      |
| `excerpt`   |          | First ~42 words of the body        | Shown on cards and in link previews.                          |

## Supported markdown

Minimal on purpose — easy to read as a plain text file, easy to extend.

- Paragraphs: blank line between
- H2: `## Heading`
- Emphasis: `*italic*`, `**bold**`
- Links: `[link text](https://example.com)`

If you need lists, images, or code blocks, extend the `markdown_to_html()`
function in `publish.py`.

## Files in this repo

```
publish.py               Publishing script (Python stdlib only)
_template.html           Article page template (placeholders: {{TITLE}}, {{ARTICLE_BODY}}, …)
_index_template.html     Homepage template (placeholders: {{FEATURED_STACK}}, {{PREV_SECTION}})
articles.json            Generated catalog. Don't edit by hand — the script rewrites it.
index.html               Generated homepage. Don't edit by hand — re-run publish.py to change layout.
chiel.jpg                Author photo used in the Card 1 avatar.
drafts/                  Your markdown drafts.
<slug>.html              Generated article pages.
```

## Editing styles

CSS lives inline in `_template.html` (article pages) and `_index_template.html`
(homepage). Edit those files — next time you run `publish.py`, the new styles
flow into regenerated pages. Already-published article HTML files won't update
until you re-run the script on each draft, so for style tweaks across all
articles, re-run every draft in `drafts/`:

```bash
for f in drafts/*.md; do python3 publish.py "$f"; done
```
