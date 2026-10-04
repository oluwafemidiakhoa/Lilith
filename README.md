# Sweet Tea Astrology

Production-prep website for **Sweet Tea Astrology**, built as a deliberately small static site on Vercel.

## Current architecture

The website itself is static HTML/CSS/JavaScript. Customer-facing operations are intended to use managed providers rather than a custom application backend:

**Website → managed scheduler → Sweet Tea Astrology payment account → Therry's calendar/Zoom → transactional reminders**

This keeps the system inexpensive, inspectable, and easier to maintain.

## Current pages

- `index.html` — homepage
- `services.html` — readings and pricing
- `booking.html` — booking plan, first class, and policies
- `about.html` — Therry's story
- `privacy.html` — customer data practices
- `policies.html` — booking and class policies

## Safety state

- Search indexing is intentionally disabled during development.
- Checkout is intentionally disabled until Sweet Tea Astrology's own payment account is connected.
- No custom customer database, payment backend, SMS service, or Zoom automation is currently running.
- Security headers are configured in `vercel.json`.
- `.github/workflows/site-checks.yml` validates local links, required files, stale copy, and common secret patterns.

See `LAUNCH_CHECKLIST.md` before enabling payments or public search indexing.
