#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(ROOT.glob("*.html"))
SELF = Path(__file__).resolve()
errors = []

REQUIRED_FILES = [
    "index.html",
    "about.html",
    "services.html",
    "booking.html",
    "privacy.html",
    "policies.html",
    "vercel.json",
    "robots.txt",
]

STALE_COPY = [
    "index.html#book",
    "Calendar integration ready",
    "First website mockup",
]

SECRET_PATTERNS = [
    (re.compile(r"sk_live_[A-Za-z0-9]{12,}"), "live Stripe secret"),
    (re.compile(r"sk_test_[A-Za-z0-9]{12,}"), "test Stripe secret"),
    (re.compile(r"sk-proj-[A-Za-z0-9_-]{12,}"), "OpenAI project key"),
    (re.compile(r"postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@"), "database URL with embedded credentials"),
    (re.compile(r"VERCEL_TOKEN\s*=\s*[^\s$<{][^\s]*"), "Vercel token assignment"),
    (re.compile(r"DATABASE_URL\s*=\s*['\"]?postgres(?:ql)?://"), "database URL assignment"),
]

SECURITY_HEADERS = {
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
}


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = []
        self.images = []
        self.blank_links = []
        self.inline_handlers = []
        self.main_count = 0
        self.html_lang = None

    def handle_starttag(self, tag, attrs):
        attrs_list = attrs
        attrs = dict(attrs_list)

        if tag == "html":
            self.html_lang = attrs.get("lang")

        if tag == "main":
            self.main_count += 1

        element_id = attrs.get("id")
        if element_id:
            self.ids.append(element_id)

        for key in ("href", "src"):
            value = attrs.get(key)
            if value:
                self.refs.append((tag, key, value))

        if tag == "img":
            self.images.append(attrs)

        if tag == "a" and attrs.get("target") == "_blank":
            self.blank_links.append(attrs)

        for key, value in attrs_list:
            if key.lower().startswith("on") and value:
                self.inline_handlers.append((tag, key))


def check_ref(source, value):
    if value.startswith(("#", "mailto:", "tel:", "data:")):
        return

    if value.lower().startswith("javascript:"):
        errors.append(f"{source.name}: javascript: URL is not allowed")
        return

    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return

    path = unquote(parts.path)
    if not path:
        return

    target = (source.parent / path).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        errors.append(f"{source.name}: local reference escapes repository root: {value!r}")
        return

    if not target.exists():
        errors.append(f"{source.name}: broken local reference {value!r}")


def check_html(file):
    text = file.read_text(encoding="utf-8")

    if "<title>" not in text:
        errors.append(f"{file.name}: missing <title>")
    if 'name="viewport"' not in text:
        errors.append(f"{file.name}: missing viewport meta")
    if 'name="robots" content="noindex,nofollow"' not in text:
        errors.append(f"{file.name}: development safety noindex is missing")

    parser = SiteParser()
    parser.feed(text)

    if parser.html_lang != "en":
        errors.append(f"{file.name}: html lang must be 'en'")

    if parser.main_count != 1:
        errors.append(f"{file.name}: expected exactly one <main>, found {parser.main_count}")

    seen = set()
    duplicate_ids = sorted({x for x in parser.ids if x in seen or seen.add(x)})
    for duplicate_id in duplicate_ids:
        errors.append(f"{file.name}: duplicate id {duplicate_id!r}")

    for _, _, ref in parser.refs:
        check_ref(file, ref)

    for attrs in parser.images:
        if "alt" not in attrs:
            errors.append(f"{file.name}: image missing alt attribute: {attrs.get('src', '<unknown>')!r}")
        if not attrs.get("width") or not attrs.get("height"):
            errors.append(f"{file.name}: image missing explicit width/height: {attrs.get('src', '<unknown>')!r}")

    for attrs in parser.blank_links:
        rel = set((attrs.get("rel") or "").lower().split())
        if not ({"noopener", "noreferrer"} & rel):
            errors.append(f"{file.name}: target=_blank link must use rel=noopener or noreferrer: {attrs.get('href', '<unknown>')!r}")

    for tag, attr in parser.inline_handlers:
        errors.append(f"{file.name}: inline event handler is not allowed: <{tag} {attr}=...>")

    for stale in STALE_COPY:
        if stale in text:
            errors.append(f"{file.name}: stale production copy remains: {stale}")


def iter_secret_scan_files():
    allowed = {".html", ".js", ".json", ".yml", ".yaml", ".md", ".txt", ".py"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == SELF:
            continue
        if any(part.startswith(".git") for part in path.parts):
            continue
        if path.suffix.lower() not in allowed:
            continue
        if path.stat().st_size > 2_000_000:
            continue
        yield path


def check_secrets():
    for path in iter_secret_scan_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                rel = path.relative_to(ROOT)
                errors.append(f"possible committed secret in {rel}: {label}")


def check_vercel_headers():
    path = ROOT / "vercel.json"
    if not path.exists():
        return

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"vercel.json: invalid JSON: {exc}")
        return

    headers = {}
    for rule in config.get("headers", []):
        if rule.get("source") == "/(.*)":
            headers.update({h.get("key"): h.get("value", "") for h in rule.get("headers", []) if h.get("key")})

    missing = sorted(SECURITY_HEADERS - set(headers))
    if missing:
        errors.append(f"vercel.json: missing security headers on /(.*): {', '.join(missing)}")

    csp = headers.get("Content-Security-Policy", "")
    for directive in ("default-src 'self'", "object-src 'none'", "frame-ancestors 'none'"):
        if directive not in csp:
            errors.append(f"vercel.json: CSP missing required directive: {directive}")


for item in REQUIRED_FILES:
    if not (ROOT / item).exists():
        errors.append(f"missing required file: {item}")

for file in HTML_FILES:
    check_html(file)

check_secrets()
check_vercel_headers()

robots = (ROOT / "robots.txt").read_text(encoding="utf-8") if (ROOT / "robots.txt").exists() else ""
if "Disallow: /" not in robots:
    errors.append("robots.txt is not blocking indexing during development")

if errors:
    print("SITE CHECKS FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"SITE CHECKS PASSED: {len(HTML_FILES)} HTML pages checked.")
