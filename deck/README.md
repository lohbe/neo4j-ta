# Neo4j — reveal.js decks

Two self-contained [reveal.js](https://revealjs.com) decks on Neo4j, tailored to
the banking fraud-detection graph in this repo. Both share one theme and one
live-preview harness.

| Deck | Open at | Source |
|------|---------|--------|
| **Technical Advisory** — infra, data mgmt, tuning, licensing, competition | <http://localhost:4321/> | `slides.md` |
| **Business & Strategy** — what/why/when/how, value & impact | <http://localhost:4321/business.html> | `business.md` |

```
deck/
├── index.html     # Technical Advisory bootstrap (CDN, no build step)
├── business.html  # Business & Strategy bootstrap
├── slides.md      # ← TA content. All content lives here, in Markdown.
├── business.md    # ← Business & Strategy content, in Markdown.
├── theme.css      # Neo4j-flavoured visual overrides (shared)
├── package.json   # live-preview harness (live-server)
└── README.md
```

## Live edit / preview loop

The deck loads `slides.md` at runtime via `fetch`, so it must be served over
HTTP (opening `index.html` as a `file://` URL will show a blank deck). Any static
server with live-reload works. Two options:

### Option A — npm (auto-reload on save)

```bash
cd deck
npm install      # one time
npm start        # serves http://localhost:4321 and reloads on save
```

Edit `slides.md` (or `theme.css`), hit save, and the browser refreshes
automatically. This is the intended authoring loop.

### Option B — zero install

```bash
cd deck
npx live-server --port=4321 --watch=slides.md,theme.css .
# or, no live-reload:
python3 -m http.server 4321
```

Then open <http://localhost:4321>.

## Authoring `slides.md`

- `===` on its own line starts a **new horizontal slide**.
- `--` on its own line starts a **vertical (sub) slide**.
- `Note:` begins **speaker notes** for the current slide (press **S** to view).
- Add a slide class with an HTML comment: `<!-- .slide: class="divider" -->`.
- Fenced code blocks get syntax highlighting (` ```cypher `, ` ```bash `, etc.).
- Inline raw HTML is allowed — used here for `.pill`, `.cols`, and `.note` helpers
  defined in `theme.css`.

## Presenting

| Key | Action |
|-----|--------|
| `Space` / `→` | next · `←` previous |
| `Esc` / `O` | slide overview |
| `S` | speaker-notes window |
| `F` | fullscreen |
| `Ctrl/Cmd + F` | search slide text |
| `?` | keyboard help |

## Export to PDF

Append `?print-pdf` to the URL and use the browser's **Print → Save as PDF**
(Chrome, background graphics on, margins none):

```
http://localhost:4321/?print-pdf
```
