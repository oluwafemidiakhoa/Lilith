# Sweet Tea Astrology — Production Launch Checklist

This project intentionally stays simple: a static Vercel site plus managed services for scheduling, payments, calendar, Zoom, email, and optional SMS. Do not replace those providers with a custom booking/payment backend unless there is a clear business need.

## Required before checkout opens

- [ ] Therry controls the Sweet Tea Astrology Stripe/payment account.
- [ ] `therry@sweetteastrology.com` can send and receive mail.
- [ ] A managed scheduling provider is selected and connected to Therry's calendar.
- [ ] Therry controls which appointment blocks are published.
- [ ] 48-hour minimum booking notice is configured.
- [ ] 15-minute buffer between private appointments is configured.
- [ ] Therry's Zoom Pro account is connected by Therry through provider authorization; no password is shared.
- [ ] November 21 class timezone is confirmed and displayed.
- [ ] First class seat limit is confirmed.
- [ ] First class registration-close rule is confirmed.
- [ ] Stripe/test checkout is tested end-to-end before live mode.
- [ ] Booking confirmation, 3-day reminder, 24-hour reminder, and final reminder are tested.
- [ ] If SMS launches on day one, explicit transactional SMS opt-in and opt-out handling are tested.
- [ ] Privacy and Booking Policies are reviewed by Therry.
- [ ] Recording notice is shown before recorded classes.
- [ ] Public reuse of identifiable attendee information requires separate permission.

## Domain and ownership

- [ ] `sweetteastrology.com` is verified in Therry/Val's registrar account.
- [ ] `sweetteastrology.com` is attached to the Vercel project.
- [ ] `www.sweetteastrology.com` redirects to the chosen canonical domain.
- [ ] Business-critical accounts remain owned by Sweet Tea Astrology / Therry.
- [ ] A clear developer handoff/recovery path exists for the GitHub and Vercel project.

## Launch-day technical checks

- [ ] GitHub Site checks workflow is green.
- [ ] Home, About, Readings, Booking, Privacy, and Policies pages load on mobile and desktop.
- [ ] All internal links work.
- [ ] Security headers are present.
- [ ] No secrets are committed to GitHub.
- [ ] Payment, cancellation, refund/reschedule, and failed-payment flows are tested.
- [ ] Customer birth information is collected only through the approved booking/intake provider.
- [ ] The website does not store card numbers.

## Search launch

The site is intentionally hidden from search while it is being built.

Only after Therry approves the public launch:

- [ ] Remove `noindex,nofollow` from public pages.
- [ ] Change `robots.txt` to allow indexing.
- [ ] Add canonical URLs and final Open Graph metadata for `sweetteastrology.com`.
- [ ] Submit the sitemap/search-console setup if desired.

## Written readings

Do not activate until Therry confirms:

- [ ] price
- [ ] exact deliverable/format
- [ ] turnaround time
- [ ] revision/follow-up policy
