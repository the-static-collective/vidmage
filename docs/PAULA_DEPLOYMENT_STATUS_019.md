# Paula deployment checkpoint 019 — Cloudflare protection prepared

## Working now
- Cloudflare zone `abundent.org` is active.
- Cloudflare Pages `paula-movie-portal` auto-deploys static files from `feature/paula-domain-017-ph-abundent`.
- `https://ph.abundent.org` is protected by existing Cloudflare Zero Trust Access application `Paula Movie Portal`. Its Pages front door provides the Kling and Flow launch links.
- **2026-10-13/14:** authenticated Cloudflare browser session created **two exact-host, self-hosted Access applications**:
  - `Paula Home Studio` for `ph-home.abundent.org` — `Paula Home Studio Policy`, Allow single owner email.
  - `Paula AWS Studio` for `ph-aws.abundent.org` — `Paula AWS Studio Policy`, Allow single owner email.
- Browser verification reported no wildcard policies or public allow-all rules.
- Neither origin hostname has DNS routing, and no public access to an unsecured renderer was created.
- Original Vercel and other existing DNS records were not changed.

## Blockers / operator wall

**Unresolved:** Cloudflare dashboard showed *session expires immediately* for both new Access applications. Verify and change each session to 24 hours before relying on iPhone authentication. OTP eligibility was not confirmed for these two new applications. A subsequent authenticated browser run to fix session durations **did not start** because the TinyFish wallet was out of funds; no settings were changed in that attempt. Do not claim the session expiry issue is fixed.

**Not provisioned:** neither Linux Home machine nor AWS EC2 has been launched. The prepared app backend is still unhosted. Separate `paula-home` and `paula-aws` Cloudflare Tunnels have **not** been created; tunnel install tokens must remain private to each machine. Do not route hostnames until the corresponding origin exists, runs on loopback `127.0.0.1:8768`, and validates Access JWT tokens.

**Not authorized:** Paula's own email identity. She must be allowlisted in BOTH node apps and the `ph.abundent.org` portal app before using the service; owner controls this in Cloudflare, and each backend must separately include her exact email in its private `PAULA_ALLOWED_EMAILS`. Do not put user identity data in this public repository.

**AWS remains a separate purchase gate:** Budget alert and explicit monthly spend choice required before launching EC2, EBS, public IPv4, Cloudflare browser sessions or other billable resources. Budget alerts are NOT hard spend caps.

## Free, usable Kling planner — 020

**Deployed and independently retrieved from public Pages (no new service bill):**

- Public static preview `https://paula-movie-portal.pages.dev/make/` resolves and renders the `Paula's Shot Notebook` page.
- Protected front door `https://ph.abundent.org/make/` remains behind Cloudflare Access; an unauthenticated external fetch returns `login_required`.
- The portal links to `/make/` as its **first working action**. Home and AWS buttons explicitly identify unavailable render nodes.
- `deploy/portal/make/index.html` and `app.js` implement a **browser-local** editor: title, story, character continuity, tone, video aspect ratio, up to 12 shots, camera direction and estimated seconds; one-copy-per-shot Kling prompts and a clip-downloaded checklist.
- Notebook automatically saves into browser localStorage and can export or restore a bounded JSON backup. The **Export for Vidmage story editor** action generates `vidmage/paula-pocket-project/v1` with NO fabricated approval receipts; the private editor will require explicit scene approval once deployed.
- Network boundaries: no `fetch`, XMLHttpRequest, WebSocket, analytics or provider API; site CSP allows **same-origin scripts** while retaining `connect-src 'none'`, `default-src 'none'`, `frame-ancestors 'none'`, and no forms. Private entries remain confined to the current browser origin, not cross-device synced. The `pages.dev` alias is public but stores no server-side story content.
- `tests/test_paula_shotkit.py` runs Node VM compilation/pure-core tests, XSS text escaping, backup import bounds, portable export shape, plus static site structure/CSP checks. GitHub workflow runs it on changes. Live iPhone interaction has NOT been browser-tested, so do not describe it as iOS E2E verified.
- Important: the two future render nodes still require an actual computer, secure Cloudflare Tunnel JWT environment, and for AWS spending approval.

**Home launch hardening:**

- `deploy/start_node.sh` now rejects empty Access config values and refuses `PAULA_AUTH_MODE=local` before starting a hosted node.
- `deploy/node_preflight.sh` checks the actual HTTP status from `127.0.0.1:8768/api/health`. A missing server is informational; 401/503 is expected fail-closed; **anonymous HTTP 200 or other unexpected responses abort preflight** before connecting a tunnel.
- No live origin was started and no tunnel/DNS routing changed in this patch.

## Next actions when operator is ready

1. Confirm whether the home machine is Ubuntu/Debian, Windows+WSL2 or macOS, always-on disk/internet situation, and whether an AWS account is configured; use `deploy/DUAL_HOST_SETUP.md` for Ubuntu instructions and `deploy/aws/paula-ec2.yaml` for infrastructure.
2. Fix Cloudflare Access session durations and check email OTP. Record **non-secret** Access application audience (AUD) and team domain for Home/AWS, and put them in each host's **private** `.env.paula` (NOT in repo).
3. On Home machine: clone this feature branch, `bash deploy/install_docker_ubuntu.sh` as applicable, initialize private env, `bash deploy/start_node.sh`; test refusal to serve without Cloudflare Access.
4. Then create/install **paula-home** remote tunnel on Home machine; route **only** `ph-home.abundent.org` to private `http://127.0.0.1:8768` after it is healthy; confirm Access rejects other identities.
5. Only with budget approval, provision AWS; create/install independent `paula-aws` tunnel; test isolation and separate receipt signing keys.
6. Test iPhone Safari end-to-end with *synthetic* pictures and Kling clip before allowing real family photos. Import flow supports manual MP4 uploads and local FFmpeg cuts; no auto Kling API operation or subscription billing.

## Security and truth
Cloudflare Access app configuration alone is NOT a running video server. The public Pages alias is a static navigation shell, not a secret/medical/media data store. Treat film outputs, owner identity, and receipts as private files, never publish them to GitHub. The two nodes currently do not synchronize projects, originals or signing keys. 
