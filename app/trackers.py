"""
trackers.py — a curated database of known third-party tracker domains.

WHY A CURATED LIST INSTEAD OF SOME CLEVER DETECTION ALGORITHM
-----------------------------------------------------------------
There's no way to detect "this is a tracker" purely from a URL's shape —
a tracker script looks exactly like any other JavaScript file. The real
privacy-blocking tools (uBlock Origin, Disconnect, Ghostery) all work the
same way under the hood: a maintained list of known tracker domains,
compiled by researching what each company's scripts actually do.

This list is a small, illustrative starting point (~30 entries) covering
the most common trackers you'll actually encounter on real websites — not
a complete replacement for a maintained list like EasyPrivacy or
Disconnect's, which have thousands of entries and dedicated maintainers.

FORMAT
-------
Each entry maps a registrable domain (e.g. "google-analytics.com") to a
(company, category) tuple. Matching also catches subdomains of these
domains (e.g. "www.google-analytics.com") — see scanner.py.
"""

TRACKER_DB = {
    # --- Google ---
    "google-analytics.com": ("Google", "Analytics"),
    "googletagmanager.com": ("Google", "Analytics"),
    "doubleclick.net": ("Google", "Advertising"),
    "googlesyndication.com": ("Google", "Advertising"),
    "googleadservices.com": ("Google", "Advertising"),
    "google.com": ("Google", "Advertising"),  # e.g. /ads/ga-audiences pixel hits

    # --- Meta / Facebook ---
    "facebook.net": ("Meta", "Social/Advertising"),
    "facebook.com": ("Meta", "Social/Advertising"),
    "connect.facebook.net": ("Meta", "Social/Advertising"),

    # --- Microsoft ---
    "clarity.ms": ("Microsoft", "Analytics"),
    "bat.bing.com": ("Microsoft", "Advertising"),
    "linkedin.com": ("Microsoft (LinkedIn)", "Advertising"),

    # --- Amazon ---
    "amazon-adsystem.com": ("Amazon", "Advertising"),

    # --- Analytics / product analytics platforms ---
    "hotjar.com": ("Hotjar", "Analytics"),
    "segment.com": ("Segment (Twilio)", "Analytics"),
    "segment.io": ("Segment (Twilio)", "Analytics"),
    "mixpanel.com": ("Mixpanel", "Analytics"),
    "amplitude.com": ("Amplitude", "Analytics"),
    "fullstory.com": ("FullStory", "Analytics"),
    "mouseflow.com": ("Mouseflow", "Analytics"),

    # --- Ad networks ---
    "criteo.com": ("Criteo", "Advertising"),
    "criteo.net": ("Criteo", "Advertising"),
    "taboola.com": ("Taboola", "Advertising"),
    "outbrain.com": ("Outbrain", "Advertising"),
    "adroll.com": ("AdRoll", "Advertising"),
    "pubmatic.com": ("PubMatic", "Advertising"),
    "rubiconproject.com": ("Magnite", "Advertising"),

    # --- Older/legacy analytics still seen in the wild ---
    "scorecardresearch.com": ("Comscore", "Analytics"),
    "quantserve.com": ("Quantcast", "Analytics"),
    "quantcast.com": ("Quantcast", "Analytics"),

    # --- Marketing / CRM platforms ---
    "hubspot.com": ("HubSpot", "Marketing"),
    "hs-analytics.net": ("HubSpot", "Marketing"),
    "intercom.io": ("Intercom", "Marketing"),
    "intercomcdn.com": ("Intercom", "Marketing"),
    "drift.com": ("Drift", "Marketing"),

    # --- Social widgets (beyond Meta/LinkedIn above) ---
    "twitter.com": ("X (Twitter)", "Social"),
    "x.com": ("X (Twitter)", "Social"),
    "pinterest.com": ("Pinterest", "Social"),
    "tiktok.com": ("TikTok", "Analytics"),

    # --- Performance monitoring (lower privacy weight — see scanner.py) ---
    "newrelic.com": ("New Relic", "Performance"),
    "nr-data.net": ("New Relic", "Performance"),
    "cloudflareinsights.com": ("Cloudflare", "Performance"),
}
