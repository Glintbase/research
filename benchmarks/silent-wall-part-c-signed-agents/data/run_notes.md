# Run notes — Silent Wall Part C (E6)

- Pre-registration frozen: commit 3ddbc9e (2026-11-04), before any request
- Key: Ed25519, kid `ZnRZwqhiD-BF30ZqAvc_CgLXsPIX1SsXKG9QJTHSrX0`; private key outside every repository (~/.glintbase/web-bot-auth/ed25519.pem)
- Key directory deploy: approved by Victor Okolie (relayed by the coordinating session, then confirmed by the user in this session on 2026-11-09). glintbase-waitlist main fast-forwarded to 38c1c83 at ~06:58Z.
- **Directory live: 2026-11-09T07:02:54Z.** `GET https://glintbase.dev/.well-known/http-message-signatures-directory` → 200, `application/http-message-signatures-directory+json`, JWKS with our one key. The directory response itself is **unsigned** (WEB_BOT_AUTH_DIRECTORY_KEY not set; that's Victor's to set). /research/bot shows the key ID and the Part C study.
- **Signature check before signed rounds (pre-registration §3):**
  - Cloudflare's reference implementation (`web-bot-auth` 0.2.0 on npm, `verify()` with the key fetched live from the directory): first attempt **rejected**, because our nonce was 32 bytes and the library requires 64. Nonce changed to 64 random bytes (harness `webbotauth.py`, before any signed study request). Re-check: **VERIFIED** (keyid, tag `web-bot-auth`, Signature-Agent `sig1` → `https://glintbase.dev`, type directory).
  - Cloudflare's public demo page (http-message-signatures-example.research.cloudflare.com), signing with the RFC 9421 test key: rejected in every header variant tried. Our keyid for the test key matches the draft's test vector (`poqkLGiymh_W0uP6PZFw-dvez3QJT5SolqXBCW38r0U`). The page cites the expired architecture draft; we treat it as out of date and rely on the reference library.
- S1 started: 2026-11-14T12:16:34Z, workers 4, vantage 102.90.126.151 (NG, ORG-MN1-AFRINIC); connectivity log data/connectivity_S1.txt
