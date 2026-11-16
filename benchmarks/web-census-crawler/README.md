# Shared web-census crawler (E1 + E3, November 2026)

One crawler pass serves two studies:
- [Content-Signal Consistency Census (E1)](../content-signal-census/) — 1,121 sites
- [The Front-Door Files Census (E3)](../front-door-files-census/) — 6,908 sites

`harness/build_sample.py` builds `data/sample.csv` from frozen inputs (no network). `harness/crawl.py` sends the requests listed in each study's pre-registration with the honest identity `GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`, obeys robots.txt for `GlintbaseResearch`, and keeps ≤ 1 request/second per site. Raw per-site records (`data/raw/`) are not published; each study's `harness/analyze.py` derives the published per-site tables.
