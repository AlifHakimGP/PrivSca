"""
scanner.py — fetch a page, find third-party trackers in it, score it.

WHAT THIS CAN AND CAN'T SEE (important limitation, stated upfront)
---------------------------------------------------------------------
This fetches the page's raw HTML and looks at <script>, <img>, <iframe>,
and <link> tags already present in that markup. It does NOT run any
JavaScript. Many real tracking requests are triggered dynamically (a
script that loads, then itself fetches more trackers at runtime) — those
are invisible to a tool like this one, the same limitation every
"static HTML scanner" has. A full solution would need a real headless
browser (e.g. Playwright) to execute the page's JS and watch actual
network requests — a good "next step" extension, deliberately left out
to keep this weekend-sized.
"""

from urllib.parse import urljoin, urlparse

import httpx
import tldextract
from bs4 import BeautifulSoup

from .trackers import TRACKER_DB

# By default, tldextract tries to fetch a *live* public-suffix list from
# the internet the first time it runs, falling back to its bundled
# snapshot only if that fails. That's a slow, unnecessary network call on
# every cold start (and noisy if it's ever blocked, e.g. by a firewall).
# suffix_list_urls=() disables the live fetch entirely — it always uses
# the bundled snapshot, which is more than accurate enough for this tool.
_tld_extractor = tldextract.TLDExtract(suffix_list_urls=())

# How much each tracker category costs you, out of a starting score of
# 100. Advertising/fingerprinting trackers are weighted heaviest since
# they're the most invasive category; performance monitoring (error
# tracking, latency metrics) is weighted lightest since it's not usually
# about tracking *you* personally.
CATEGORY_WEIGHTS = {
    "Advertising": 12,
    "Social/Advertising": 12,
    "Fingerprinting": 15,
    "Analytics": 8,
    "Social": 7,
    "Marketing": 7,
    "Performance": 3,
}


def get_registrable_domain(hostname: str) -> str:
    """
    Turn 'www.ads.google-analytics.com' into 'google-analytics.com'.

    A plain string split on '.' breaks on domains like 'co.uk' (you'd
    get 'uk' instead of 'example.co.uk'). tldextract knows the real list
    of public suffixes (.com, .co.uk, .com.au, etc.) and splits correctly.
    """
    if not hostname:
        return ""
    ext = _tld_extractor(hostname)
    if not ext.domain:
        return hostname
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain


def find_tracker(domain: str):
    """Look up a registrable domain in the tracker database."""
    return TRACKER_DB.get(domain)


def compute_score(trackers_found: list[dict]) -> tuple[int, str]:
    score = 100
    for t in trackers_found:
        score -= CATEGORY_WEIGHTS.get(t["category"], 6)
    score = max(0, score)

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 55:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"
    return score, grade


async def scan_url(url: str) -> dict:
    headers = {
        # A real browser-like user agent: some sites serve different (or
        # no) content to obvious bots, which would make this tool useless
        # against exactly the sites most worth checking.
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        final_url = str(resp.url)  # after following any redirects
        html = resp.text

    target_domain = get_registrable_domain(urlparse(final_url).hostname or "")

    soup = BeautifulSoup(html, "html.parser")
    resource_tags = (
        soup.find_all("script", src=True)
        + soup.find_all("img", src=True)
        + soup.find_all("iframe", src=True)
        + soup.find_all("link", href=True)
    )

    seen_domains = set()
    trackers_found = []
    total_resources = 0

    for tag in resource_tags:
        raw_url = tag.get("src") or tag.get("href")
        if not raw_url:
            continue
        total_resources += 1

        absolute_url = urljoin(final_url, raw_url)
        hostname = urlparse(absolute_url).hostname
        if not hostname:
            continue

        domain = get_registrable_domain(hostname)
        if domain == target_domain:
            continue  # first-party resource — not what we're looking for
        if domain in seen_domains:
            continue  # count each tracker company once, not once per script tag

        info = find_tracker(domain)
        if info:
            seen_domains.add(domain)
            company, category = info
            trackers_found.append({"domain": domain, "company": company, "category": category})

    trackers_found.sort(key=lambda t: t["category"])
    score, grade = compute_score(trackers_found)

    return {
        "url": final_url,
        "total_resources_checked": total_resources,
        "tracker_count": len(trackers_found),
        "unique_companies": len({t["company"] for t in trackers_found}),
        "trackers": trackers_found,
        "score": score,
        "grade": grade,
    }
