"""Web Bot Auth request signing (HTTP Message Signatures, RFC 9421, Ed25519).

Follows draft-meunier-webbotauth-httpsig-protocol-02 (2026-08-18) §5.2:
  - covered components: "@authority" and "signature-agent";key="<label>"
  - @signature-params: created, expires, keyid (base64url JWK SHA-256 thumbprint, RFC 7638/8037),
    alg="ed25519", nonce (random, 32 bytes base64), tag="web-bot-auth"
  - Signature-Agent sent in the dictionary form keyed by the signature label

The public key is published as a JWK Set at
https://glintbase.dev/.well-known/http-message-signatures-directory
(draft-meunier-webbotauth-httpsig-directory-00).

The private key never enters the repository. Its path comes from GLINTBASE_WBA_KEY, defaulting to
~/.glintbase/web-bot-auth/ed25519.pem.

Usage:
  python webbotauth.py keygen          # create the key (once) and print the public JWKS
  python webbotauth.py jwks            # print the public JWKS
  python webbotauth.py selftest        # sign and verify a request locally
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

SIGNATURE_AGENT = "https://glintbase.dev"
LABEL = "sig1"
TAG = "web-bot-auth"
VALIDITY_S = 300
KEY_PATH = Path(os.environ.get("GLINTBASE_WBA_KEY", Path.home() / ".glintbase" / "web-bot-auth" / "ed25519.pem"))


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def load_key(path: Path = KEY_PATH) -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def public_jwk(pub: Ed25519PublicKey) -> dict:
    raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return {"kty": "OKP", "crv": "Ed25519", "x": b64u(raw)}


def thumbprint(jwk: dict) -> str:
    # RFC 7638: required members only, lexicographic order, no whitespace (RFC 8037 A.3 for OKP).
    canon = json.dumps({"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"]}, separators=(",", ":"), sort_keys=True)
    return b64u(hashlib.sha256(canon.encode()).digest())


def jwks(key: Ed25519PrivateKey) -> dict:
    jwk = public_jwk(key.public_key())
    return {"keys": [{**jwk, "kid": thumbprint(jwk), "use": "sig"}]}


def authority(url: str) -> str:
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    default = {"https": 443, "http": 80}.get(p.scheme)
    return host if p.port in (None, default) else f"{host}:{p.port}"


def sign_headers(key: Ed25519PrivateKey, url: str, now: int | None = None, nonce: str | None = None) -> dict:
    """Headers to add to one request for `url`."""
    created = int(now if now is not None else time.time())
    nonce = nonce or base64.b64encode(secrets.token_bytes(32)).decode()
    kid = thumbprint(public_jwk(key.public_key()))
    agent_value = f'"{SIGNATURE_AGENT}"'
    params = (f'("@authority" "signature-agent";key="{LABEL}");created={created};expires={created + VALIDITY_S}'
              f';keyid="{kid}";alg="ed25519";nonce="{nonce}";tag="{TAG}"')
    base = "\n".join([
        f'"@authority": {authority(url)}',
        f'"signature-agent";key="{LABEL}": {agent_value}',
        f'"@signature-params": {params}',
    ])
    sig = base64.b64encode(key.sign(base.encode())).decode()
    return {
        "Signature-Agent": f"{LABEL}={agent_value}",
        "Signature-Input": f"{LABEL}={params}",
        "Signature": f"{LABEL}=:{sig}:",
    }


def verify_headers(pub: Ed25519PublicKey, url: str, headers: dict) -> bool:
    """Minimal verifier for our own header shape (self-test only)."""
    params = headers["Signature-Input"].split("=", 1)[1]
    agent_value = headers["Signature-Agent"].split("=", 1)[1]
    base = "\n".join([
        f'"@authority": {authority(url)}',
        f'"signature-agent";key="{LABEL}": {agent_value}',
        f'"@signature-params": {params}',
    ])
    sig = base64.b64decode(headers["Signature"].split("=", 1)[1].strip(":"))
    try:
        pub.verify(sig, base.encode())
        return True
    except Exception:
        return False


def httpx_signing_hook(key: Ed25519PrivateKey):
    """httpx request event hook: signs every request, including each redirect hop."""
    async def hook(request):
        for k, v in sign_headers(key, str(request.url)).items():
            request.headers[k] = v
    return hook


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "jwks"
    if cmd == "keygen":
        if KEY_PATH.exists():
            sys.exit(f"key already exists at {KEY_PATH}")
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        k = Ed25519PrivateKey.generate()
        KEY_PATH.write_bytes(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                             serialization.NoEncryption()))
        print(json.dumps(jwks(k), indent=2))
    elif cmd == "jwks":
        print(json.dumps(jwks(load_key()), indent=2))
    elif cmd == "selftest":
        k = load_key()
        h = sign_headers(k, "https://www.example.com/path?q=1")
        ok = verify_headers(k.public_key(), "https://www.example.com/other", h)
        bad = verify_headers(k.public_key(), "https://example.org/", h)
        print(json.dumps(h, indent=2))
        print("verify same authority:", ok, "| verify other authority (must be False):", bad)
        sys.exit(0 if ok and not bad else 1)


if __name__ == "__main__":
    main()
