# Privacy Scanner

Paste a URL, get back: which third-party companies would be watching you
on that page, and a plain privacy score.a single FastAPI backend + a plain
HTML/CSS/JS frontend, no build step at all.

## What it actually does — and its real limitation

It fetches the page's raw HTML and looks for `<script>`, `<img>`,
`<iframe>`, and `<link>` tags that point at known tracker domains. It
does **not** run any JavaScript on the page.

This matters: a lot of real tracking happens dynamically — a script loads,
and *that* script then fetches more trackers at runtime, or injects more
tags into the page after load. None of that is visible to a tool that
only reads the initial HTML. This is the same fundamental limitation every
purely-static scanner has; a complete version would need a real headless
browser (Playwright/Puppeteer) to execute the page and watch actual
network traffic — a solid "next step" if you want to extend this, but
deliberately left out here to keep it weekend-sized. The frontend's
footer note says this plainly so nobody mistakes the score for a complete
audit.

## How it works

### Finding trackers — a curated list, like every real privacy tool

There's no way to detect "this is a tracker" from a URL's *shape* — a
tracking script looks exactly like any other JavaScript file syntactically.
Real tools (uBlock Origin, Disconnect, Ghostery) all work the same way
under the hood: someone maintains a list of known tracker domains. This
project's list (`app/trackers.py`) is a small, illustrative ~30-domain
starting point covering the most common real-world trackers (Google,
Meta, Hotjar, Mixpanel, Criteo, etc.) — not a complete replacement for a
maintained list with thousands of entries.

### Correctly identifying "the same domain" — why `tldextract`

A naive approach (`hostname.split('.')[-2:]`) breaks on domains like
`example.co.uk` — you'd get `co.uk` instead of `example.co.uk`, and wrongly
treat every `.co.uk` site as "the same domain." `tldextract` knows the
real list of public suffixes and splits correctly. It's pinned to
offline-only mode (`suffix_list_urls=()`) so it never tries a live
network fetch on startup — it uses its bundled snapshot, which is both
faster and avoids a noisy failure if that network call is ever blocked.

### The scoring model

Starts at 100, subtracts points per tracker found, weighted by category:

| Category | Points off | Why |
|---|---|---|
| Fingerprinting | 15 | Most invasive — identifies you across sites without cookies |
| Advertising / Social-Advertising | 12 | Core ad-tracking business model |
| Analytics / Social / Marketing | 7–8 | Tracks behavior, less identity-focused |
| Performance (error/latency monitoring) | 3 | Usually not about tracking *you* specifically |

Each tracker **company** is only counted once per scan even if it appears
in multiple tags (e.g. both a Meta pixel `<img>` and a Facebook SDK
`<script>` only cost you one Meta penalty, not two).

### First-party vs. third-party

A resource is only flagged if its registrable domain differs from the
page's own domain — a site's own `app.js` or `logo.png` is never treated
as a tracker, however the URL is written (absolute or relative; relative
paths are resolved against the final URL after redirects via
`urllib.parse.urljoin`).

## Two interfaces, one shared core

This project ships with **both** a web UI and a terminal UI — `app/scanner.py`
and `app/trackers.py` are the actual scanning/scoring logic, and neither
frontend touches that logic directly beyond calling `scan_url()`. This is
a useful pattern on its own: the backend doesn't know or care whether a
browser, a terminal, or a plain script is driving it.

### Terminal UI (`tui.py`) — built with Textual

```bash
pip install -r requirements.txt --break-system-packages
python3 tui.py
```

Type a URL, press Enter (or click **Scan**), see the grade, score, and
tracker table right in your terminal. `q` or `Ctrl+C` to quit.

This uses [Textual](https://textual.textualize.io/), a modern Python TUI
framework from the same team behind the `rich` library — it gives you a
real widget system (`Input`, `Button`, `DataTable`), CSS-like styling, and
native async support, rather than hand-rolling character positions with
the low-level `curses` module. The async support specifically matters
here: `scan_url()` awaits a network request, and Textual's `@work`
decorator runs that in the background so the UI stays responsive (not
frozen) while it waits.

### Web UI (`app/main.py` + `static/index.html`)

```bash
docker build -t privacy-scanner .
docker run -p 8000:8000 privacy-scanner
```

or locally:

```bash
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` and paste a URL.

## API reference

```
POST /api/scan
  body: { "url": "example.com" }   (scheme optional — https:// assumed if missing)

  response: {
    "url": "...",                   // final URL after following redirects
    "total_resources_checked": 9,
    "tracker_count": 5,
    "unique_companies": 3,
    "trackers": [
      { "domain": "doubleclick.net", "company": "Google", "category": "Advertising" },
      ...
    ],
    "score": 48,
    "grade": "D"
  }
```

## Extending this project

- **Expand the tracker list** — the biggest single improvement. A real
  maintained list (e.g. Disconnect's open-source tracker list on GitHub)
  has thousands of entries versus this project's ~30.
- **Headless-browser mode** — swap the `httpx` fetch for Playwright to
  execute JavaScript and capture the *actual* network requests a page
  makes, not just what's in the initial HTML. This is the single biggest
  accuracy improvement possible, at the cost of real complexity (a
  browser binary, much slower scans).
- **Fingerprinting detection** — check for known fingerprinting script
  signatures (canvas fingerprinting, `navigator.hardwareConcurrency`
  probing, etc.) rather than just domain matching.
- **Scan history** — store past scans (SQLite, same pattern as
  `push-dashboard`) so people can compare a site's score over time.
- **Batch scanning** — accept a list of URLs instead of one at a time.

## Troubleshooting

- **Every scan returns "Couldn't reach that URL"** — check the target
  site isn't blocking requests with no real browser behind them; some
  sites reject requests whose `User-Agent` looks automated beyond just
  the string we send (JS challenges, Cloudflare bot checks, etc.) — a
  known limitation of not running a real browser.
- **A site you know has trackers shows a clean "A"** — likely means its
  trackers are loaded dynamically by JavaScript rather than present in
  the initial HTML (see "real limitation" above), or it uses a tracker
  domain not yet in `app/trackers.py`.
