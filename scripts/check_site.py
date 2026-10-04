#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(ROOT.glob("*.html"))
errors = []

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            value = attrs.get(key)
            if value:
                self.refs.append((tag, key, value))

def check_ref(source, value):
    if value.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return
    path = parts.path
    if not path:
        return
    target = (source.parent / path).resolve()
    if not target.exists():
        errors.append(f"{source.name}: broken local reference {value!r}")

for file in HTML_FILES:
    text = file.read_text(encoding="utf-8")
    if "<title>" not in text:
        errors.append(f"{file.name}: missing <title>")
    if 'name="viewport"' not in text:
        errors.append(f"{file.name}: missing viewport meta")
    if 'name="robots" content="noindex,nofollow"' not in text:
        errors.append(f"{file.name}: development safety noindex is missing")
    parser = LinkParser()
    parser.feed(text)
    for _, _, ref in parser.refs:
        check_ref(file, ref)

required = ["index.html", "about.html", "services.html", "booking.html", "privacy.html", "policies.html", "vercel.json", "robots.txt"]
for item in required:
    if not (ROOT / item).exists():
        errors.append(f"missing required file: {item}")

all_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in ROOT.rglob("*") if p.is_file() and p.stat().st_size < 2_000_000)
for pattern, label in [
    (r"sk_live_[A-Za-z0-9]+", "live Stripe secret"),
    (r"sk_test_[A-Za-z0-9]+", "test Stripe secret"),
    (r"VERCEL_TOKEN\s*=", "Vercel token assignment"),
    (r"DATABASE_URL\s*=", "database URL assignment"),
]:
    if re.search(pattern, all_text):
        errors.append(f"possible committed secret: {label}")

for stale in ["index.html#book", "Calendar integration ready", "First website mockup"]:
    if stale in all_text:
        errors.append(f"stale production copy remains: {stale}")

robots = (ROOT / "robots.txt").read_text(encoding="utf-8") if (ROOT / "robots.txt").exists() else ""
if "Disallow: /" not in robots:
    errors.append("robots.txt is not blocking indexing during development")

if errors:
    print("SITE CHECKS FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"SITE CHECKS PASSED: {len(HTML_FILES)} HTML pages checked.")
