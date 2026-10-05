# Sweet Tea Astrology Production Hardening Audit

Audit baseline: `main` at `8493efb055ff9397876cf02c5e6d19ebcb7fd3f3`.

## Executive Summary

- Readiness score: **72/100**
- Confidence: **Medium**
- Production recommendation: **Conditionally ready as a static brochure site; not ready for broader launch/checkout until release controls and launch integrations are gated**
- Highest verified risk: **Production deploys from `main` even while the repository's only CI check is failing, and `main` has no branch protection/ruleset**
- Immediate next action: **Restore trustworthy CI on a non-production branch, verify it through a PR preview, then require the green check before any future production merge**

The score reflects a deliberately small static architecture with no active database, payment backend, authentication system, AI provider, queue, or customer-data API. That reduces attack surface materially. The main current weakness is release control: regression checks are not functioning as a gate even though every push to `main` is automatically deployed to production.

## Architecture Map

```
VISITOR
  |
  v
VERCEL EDGE / STATIC HOSTING
  |
  +--> index.html / about.html / services.html / booking.html / privacy.html / policies.html
  |
  +--> local CSS, local JS, local images

SOURCE / RELEASE PATH
GitHub public repo -> main branch -> Vercel production deployment

PLANNED BUT NOT ACTIVE
managed scheduler -> payment provider -> calendar/Zoom -> email/SMS reminders
```

Trust boundaries:
- Browser <-> Vercel static content
- GitHub source/release controls <-> Vercel production deployment
- Future third-party scheduling/payment/messaging providers are not active yet

Stateful/privileged components currently active: **none in the application itself**.

## Critical / High Findings

### REL-01 Production deploys are not gated by green CI — HIGH — Verified

- **Evidence:** GitHub reports `main` as unprotected; repository rulesets are empty. The latest 10 `main` Site checks runs all concluded `failure`. Vercel nevertheless created READY production deployments from those same `main` commits.
- **Failure scenario:** a broken page, unsafe config, stale production copy, or future secret-detection failure can still be shipped immediately.
- **Impact:** availability/regression/security-control bypass.
- **Fix:** require pull requests plus the Site checks status before merge to `main`; keep Vercel preview validation on the PR branch; only merge after validation.
- **Affected:** GitHub repository release controls, Vercel Git deployment path.
- **Blast radius:** medium — release process only, not site behavior.
- **Validation:** a PR with a deliberately failing check must be blocked from merge; a green PR must produce a valid preview before merge.
- **Rollback:** remove/relax the repository rule if it blocks an emergency release.
- **Current limitation:** the connected GitHub integration can read that `main` is unprotected but cannot administer branch protection (403). This must be enabled with repository-admin access before the next production promotion.

## Medium / Low Findings

### CI-01 Site validator is self-failing — MEDIUM — Verified

- **Evidence:** `scripts/check_site.py` joins repository text including itself, then checks for three exact stale-copy strings. Code search shows all three strings exist only inside the checker itself. The latest failed check has exactly three annotations and fails in the “Validate static site” step.
- **Failure scenario:** CI is permanently red and cannot distinguish a healthy change from a bad one.
- **Impact:** false alarms, ignored CI, release-gate erosion.
- **Fix:** separate secret scanning from customer-copy scanning and exclude the checker from self-triggering stale-copy rules.
- **Affected:** `scripts/check_site.py`.
- **Blast radius:** low.
- **Validation:** PR Site checks pass on the current site and fail when a stale phrase is intentionally placed in an HTML page.
- **Rollback:** revert the checker commit.

### QA-01 Regression coverage does not test browser/layout behavior — MEDIUM — Verified

- **Evidence:** the only CI job runs one Python static checker. It checks local references, a few secret patterns, noindex, required files, and stale strings; it does not validate duplicate IDs, image accessibility metadata, unsafe target-blank links, inline event handlers, security-header configuration, or rendered responsive layout.
- **Failure scenario:** visual or semantic regressions can pass repository checks.
- **Impact:** customer-facing regressions and accessibility issues.
- **Fix:** strengthen static invariants now; add preview/browser smoke checks when an authenticated preview runner is available.
- **Affected:** `scripts/check_site.py`, CI workflow.
- **Blast radius:** low.
- **Validation:** focused negative fixtures or temporary branch edits cause the appropriate check to fail.
- **Rollback:** revert the added validations individually.

### PERF-01 Large raster images increase page weight — MEDIUM — Verified

- **Evidence:** `site.png` is ~2.25 MB and is loaded with `fetchpriority="high"` on About; `ChatGPT Image Sep 27, 2026, 09_44_50 AM.png` is ~2.35 MB and is used on Home/About. The main hero WebP is only ~65 KB.
- **Failure scenario:** slower first visit on mobile connections, especially the About hero.
- **Impact:** performance and user experience.
- **Fix:** create visually equivalent WebP/AVIF derivatives and update references after visual comparison.
- **Affected:** About/Home images and markup.
- **Blast radius:** low if image dimensions/quality are preserved.
- **Validation:** image quality comparison plus reduced transferred bytes and correct dimensions.
- **Rollback:** restore original image references.
- **Status:** deferred until the source images can be safely recompressed and visually verified in preview.

### OPS-01 Observability state cannot be fully verified — LOW / UNKNOWN

- **Evidence:** Vercel project/deployment metadata is readable, but runtime-error and drain endpoints return 403 for the connected scope.
- **Failure scenario:** future server-side features could lack usable incident telemetry.
- **Impact:** low today because the site is static; higher if APIs/payments are added.
- **Fix:** re-authenticate the Vercel connector to the owning team before backend features launch, then verify analytics/logging/error visibility.
- **Validation:** read access to project observability and a known test event.
- **Rollback:** not applicable.

### DEBT-01 Dead/legacy hero code and assets remain — LOW — Verified

- **Evidence:** `index.html` still contains unused `.hero-photo` CSS pointing at `assets/porch-scene-two-teas.webp`; several old assets are no longer referenced by live markup.
- **Failure scenario:** future edits accidentally revive a stale/corrupt path or create confusion during maintenance.
- **Impact:** maintainability and regression risk.
- **Fix:** remove only code/assets proven unused after the higher-priority controls are green.
- **Blast radius:** low, but deferred to avoid mixing cleanup with release-control fixes.

## Unknowns Blocking Confidence

- Branch protection/ruleset **can be observed as absent**, but the connected integration cannot administer or verify a future rule because repository-administration permission is unavailable.
- Vercel drains/runtime-error visibility cannot be verified through the current connector scope.
- Final production domain `sweetteastrology.com` is not attached to this Vercel project yet; launch DNS/canonical/redirect behavior remains unverified.
- Payment, scheduler, SMS, and Zoom integrations are intentionally not active, so their security/idempotency/webhook/privacy controls cannot yet be audited.

## Healthy Controls to Preserve

- Static architecture: no active custom API, database, auth system, queue, payment backend, or AI runtime.
- No Vercel project environment variables are currently configured.
- Repository code search found no committed live/test Stripe secret, API key, or database URL; secret-like matches are checker patterns/documentation only.
- Checkout/registration is intentionally disabled.
- Search indexing is intentionally blocked by page-level `noindex,nofollow` plus `robots.txt Disallow: /`.
- `vercel.json` configures CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, and Permissions-Policy.
- GitHub Actions uses minimal `contents: read` permission.
- Vercel preview/deployment protection is enabled via SSO for protected deployment types.
- A launch checklist already separates “site exists” from “payments/search are ready.”

## Domain Assessment

- **Environment isolation:** Healthy for current static scope; no app env vars or stateful services. No custom staging environment, but branch previews exist.
- **Secrets/IAM:** Healthy for current scope; no project env vars and no verified committed credentials.
- **Authentication/authorization:** Not applicable yet.
- **API safety:** Not applicable; no custom API.
- **Database:** Not applicable.
- **External dependencies:** Planned, not active.
- **Background jobs:** Not applicable.
- **Payments:** Deliberately disabled; launch controls remain future work.
- **AI/LLM economics:** Not applicable.
- **Observability:** Limited/unknown; low current impact because site is static.
- **CI/CD:** Weak — highest current risk.
- **Backups/recovery:** Git history + Vercel rollback candidates provide code/deploy rollback; no stateful application data exists.
- **Dependencies/supply chain:** Very small dependency surface; CI uses official GitHub actions and Python stdlib.
- **Performance:** Mostly lightweight except two multi-megabyte PNGs.
- **Data privacy:** Strong minimization today because the site does not collect customer data.
- **Technical debt:** Some old hero CSS/assets remain.
- **Operations:** Rollback candidates exist; release gating is not enforced.
- **Unit economics:** Current static hosting has minimal variable application cost; paid workflows are not live.

## Prioritized Remediation Roadmap

| Priority | Finding | Action | Verification | Production gate |
|---|---|---|---|---|
| P1 | CI-01 | Fix self-failing validator | PR check passes; negative stale-copy test fails | blocked until verified |
| P1 | REL-01 | Establish PR + required-check release gate | failing PR cannot merge | requires repo-admin control |
| P2 | QA-01 | Expand static safety/accessibility/config checks | focused CI tests | preview only |
| P2 | PERF-01 | Recompress large PNGs | visual + byte-size comparison | preview only |
| P3 | DEBT-01 | Remove proven dead hero code/assets | full site check + preview smoke | preview only |
| P3 | OPS-01 | Re-auth Vercel observability scope | logs/errors/drains readable | before backend launch |

## Hardening Ledger

| ID | Severity | Status | Evidence | Change | Tests | Staging | Rollback | Production |
|---|---|---|---|---|---|---|---|---|
| REL-01 | HIGH | open | main unprotected; no rulesets; production auto-deploys from main | none; blocked by missing repo-admin permission | CI now green on hardening PR | preview READY; protected preview could not be browser-smoked due Vercel connector scope | repo rule reversal | untouched |
| CI-01 | MEDIUM | verified | checker scanned its own stale literals | checker now excludes itself from stale/secret scans and scopes stale-copy checks to HTML | GitHub Site checks SUCCESS on PR run 37312376441 | preview deployment READY | revert checker commit | untouched |
| QA-01 | MEDIUM | verified | original checker covered only links/noindex/basic patterns | added duplicate-id, image metadata, target=_blank, inline-handler, path-escape and security-header/CSP checks | GitHub Site checks SUCCESS on PR run 37312376441 | preview deployment READY | revert validation commit | untouched |
| PERF-01 | MEDIUM | deferred | 2.25 MB + 2.35 MB PNGs in live pages | none | pending | pending | restore refs | untouched |
| OPS-01 | LOW/UNKNOWN | deferred | Vercel observability endpoints 403 | none | n/a | n/a | n/a | untouched |
| DEBT-01 | LOW | deferred | unused hero CSS/assets | none | pending | pending | revert cleanup | untouched |

## Final Decision

The current application is comparatively safe because it is a static, non-transactional site with strong data minimization. It is **not yet release-hardened**: the current production path accepts direct `main` changes even while CI is red. The first remediation tranche restored trustworthy CI on a non-production branch and verified it in draft PR #1. Production remains unchanged. The next production gate is repository administration: require PRs plus the green Site checks status on `main` before any future production merge.
