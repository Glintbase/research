# The Silent Wall — summary (round 1)

Domains: 150

## RQ2 Homepage challenged or blocked, by identity

- **agent**: 16.0% (24/150; CI 11.0–22.7)
- **script**: 18.7% (28/150; CI 13.2–25.7)
- **browser**: 18.7% (28/150; CI 13.2–25.7)

| Outcome (homepage) | agent | script | browser |
|---|---|---|---|
| block | 8.7% (13/150; CI 5.1–14.3) | 11.3% (17/150; CI 7.2–17.4) | 10.7% (16/150; CI 6.7–16.6) |
| challenge | 7.3% (11/150; CI 4.1–12.7) | 7.3% (11/150; CI 4.1–12.7) | 8.0% (12/150; CI 4.6–13.5) |
| rate_limited | 1.3% (2/150; CI 0.4–4.7) | 2.0% (3/150; CI 0.7–5.7) | 0.0% (0/150; CI 0–2.5) |
| error | 9.3% (14/150; CI 5.6–15.1) | 10.0% (15/150; CI 6.2–15.8) | 22.0% (33/150; CI 16.1–29.3) |
| thin | 3.3% (5/150; CI 1.4–7.6) | 4.0% (6/150; CI 1.8–8.5) | 1.3% (2/150; CI 0.4–4.7) |
| other | 1.3% (2/150; CI 0.4–4.7) | 2.0% (3/150; CI 0.7–5.7) | 0.7% (1/150; CI 0.1–3.7) |
| ok | 68.0% (102/150; CI 60.2–74.9) | 63.3% (95/150; CI 55.4–70.6) | 57.3% (86/150; CI 49.3–65.0) |
| self_excluded | 0.7% (1/150; CI 0.1–3.7) | 0.0% (0/150; CI 0–2.5) | 0.0% (0/150; CI 0–2.5) |

Paired comparisons (homepage challenged/blocked; excluding errors and self-exclusions):

- agent_vs_browser: {'paired_domains': 114, 'only_agent_blocked': 2, 'only_browser_blocked': 7, 'mcnemar_exact_p': 0.1797}
- agent_vs_script: {'paired_domains': 131, 'only_agent_blocked': 2, 'only_script_blocked': 6, 'mcnemar_exact_p': 0.2891}
- script_vs_browser: {'paired_domains': 115, 'only_script_blocked': 5, 'only_browser_blocked': 6, 'mcnemar_exact_p': 1.0}

## RQ1 robots.txt

- robots.txt fetched: 93.3% (140/150; CI 88.2–96.3); present among fetched: 86.4% (121/140; CI 79.8–91.1)

| Token | Vendor | Purpose | Named | Disallows `/` |
|---|---|---|---|---|
| GPTBot | OpenAI | training | 22.9% (32/140; CI 16.7–30.5) | 14.3% (20/140; CI 9.4–21.0) |
| OAI-SearchBot | OpenAI | search | 16.4% (23/140; CI 11.2–23.4) | 5.7% (8/140; CI 2.9–10.9) |
| ChatGPT-User | OpenAI | user | 17.9% (25/140; CI 12.4–25.0) | 7.9% (11/140; CI 4.4–13.5) |
| ClaudeBot | Anthropic | training | 25.0% (35/140; CI 18.6–32.8) | 17.1% (24/140; CI 11.8–24.2) |
| Claude-SearchBot | Anthropic | search | 12.1% (17/140; CI 7.7–18.6) | 7.9% (11/140; CI 4.4–13.5) |
| Claude-User | Anthropic | user | 13.6% (19/140; CI 8.9–20.2) | 9.3% (13/140; CI 5.5–15.2) |
| PerplexityBot | Perplexity | search | 22.9% (32/140; CI 16.7–30.5) | 12.9% (18/140; CI 8.3–19.4) |
| Perplexity-User | Perplexity | user | 14.3% (20/140; CI 9.4–21.0) | 8.6% (12/140; CI 5.0–14.4) |
| Google-Extended | Google | training | 18.6% (26/140; CI 13.0–25.8) | 11.4% (16/140; CI 7.2–17.8) |
| Googlebot | Google | search-control | 14.3% (20/140; CI 9.4–21.0) | 0.0% (0/140; CI 0–2.7) |
| Applebot-Extended | Apple | training | 19.3% (27/140; CI 13.6–26.6) | 14.3% (20/140; CI 9.4–21.0) |
| CCBot | Common Crawl | training | 22.1% (31/140; CI 16.1–29.7) | 18.6% (26/140; CI 13.0–25.8) |
| Meta-ExternalAgent | Meta | training | 18.6% (26/140; CI 13.0–25.8) | 13.6% (19/140; CI 8.9–20.2) |
| Bytespider | ByteDance | training | 22.9% (32/140; CI 16.7–30.5) | 19.3% (27/140; CI 13.6–26.6) |

Any token of a purpose disallowed at `/`: training: 23.6% (33/140; CI 17.3–31.2), search: 13.6% (19/140; CI 8.9–20.2), user: 12.1% (17/140; CI 7.7–18.6), search-control: 0.0% (0/140; CI 0–2.7)

## RQ3 Policy allows, edge blocks

- Agent challenged/blocked although robots.txt allows it: 17.2% (23/134; CI 11.7–24.4)
- …while the headless browser got the page: 1.5% (2/134; CI 0.4–5.3)

## RQ4 by sector (homepage challenged/blocked)

| sector | n | agent | script | browser |
|---|---|---|---|---|
| devtools | 30 | 6.7% | 10.0% | 3.3% |
| ecommerce | 30 | 30.0% | 30.0% | 26.7% |
| finance | 30 | 6.7% | 6.7% | 6.7% |
| media | 30 | 23.3% | 33.3% | 36.7% |
| saas | 30 | 13.3% | 13.3% | 20.0% |

## RQ4 by vendor (homepage challenged/blocked)

| vendor | n | agent | script | browser |
|---|---|---|---|---|
| akamai | 26 | 34.6% | 42.3% | 50.0% |
| cloudflare | 35 | 17.1% | 20.0% | 14.3% |
| cloudfront | 23 | 13.0% | 13.0% | 17.4% |
| datadome | 3 | 66.7% | 66.7% | 66.7% |
| fastly | 10 | 20.0% | 20.0% | 20.0% |
| other/unknown | 46 | 4.3% | 6.5% | 4.3% |
| vercel | 7 | 0.0% | 0.0% | 0.0% |

Unreachable for every identity: 11 domains

