# Vidmage / Paula Cloud 015 — private iPhone control desk

**Status: executable local prototype, no deployed URL.** This is a server for the mobile `paula/index.html` planner. It accepts an owner-approved story, optional private photos/audio, renders a real 720p FFmpeg scene-card MP4, checks the output bytes, and produces an authenticated owner-scoped receipt trail. No external generative AI service is called by the MP4 engine.

## Architecture

```text
Paula's iPhone · Safari / installed Home Screen app
  → private HTTPS domain via Cloudflare Access and Tunnel
  → owner-authenticated FastAPI service (loopback-only exposure)
  → SQLite project + receipt store / private original media copies
  → queue (one active render) → FFmpeg and Pillow → verified MP4
  → protected iPhone video preview / download / receipt export

Separate, optional, creator-initiated Flow handoff:
  → Google Flow Music (official web/app) or
  → Cloudflare Browser Run interactive Live View (optional token+metering)
```

### Security

- Default authentication mode **fails closed** without a correctly verified Cloudflare Access JWT: signature, RS256 algorithm, issuer, audience, expiry, and exact allowed email are checked. The server does not trust an unverified email header.
- Only permit `PAULA_AUTH_MODE=local` on 127.0.0.1 for tests; it intentionally isn't an internet authorization mode.
- The Docker Compose port is bound to the host **loopback** only. Use Cloudflare Tunnel to publish it; do not expose port 8768 publicly.
- No Google login/session information is stored. Remote Browser Run control links contain secret signed tokens. They are returned only to the authenticated owner after a separate affirmative action. No browser session is created on app load. Avoid sharing screenshots with the browser session link visible.
- Private stories, photos, receipts, media, and SQLite files belong exclusively in `paula-private-data` on a secured volume. Never commit them to GitHub. Back up and encrypt the volume; don't rely on a phone's local Safari storage as the sole record.
- Frontend and backend do not publicize, post, buy credits, or invoke any external model generator automatically.
- Images are decoded, orientation-fixed, resized and re-encoded server-side to strip metadata including EXIF. Audio is decoded and bounded before admission. Media never enters a shell command.
- Receipts are chained SHA-256 + server-secret HMAC. Their integrity is verifiable locally if the server key is kept; they do not certify artistic quality, rights, or consent from anyone depicted.

### Honest capability boundary

**This machine renders a real MP4**, but its default source picture video is *not* Veo or Flow AI footage. It uses user assets and story cards. The current native Vidmage BAND-IQ 010–013 compositor is a separate pinned local renderer with deeper donor dependencies. The 015 server does not claim to run it yet. Portable receipts can enter Vidmage 014's HOLD lane for owner review.

The optional Cloudflare Live View launches a temporary remote Chromium tab at `https://www.flowmusic.app/`, not an iframe or a custom impersonating Flow UI. Flow login and generation remain manual. OAuth and third-party features may not work in managed browsers; Cloudflare charges usage and sessions can expire. Direct Flow access from the phone is the reliable fallback.

## Local development/test

```sh
sudo apt install ffmpeg fonts-dejavu-core # Debian/Ubuntu example
python -m pip install -r paula_cloud/requirements.txt pytest httpx
PAULA_AUTH_MODE=local python -m paula_cloud.server
# Open http://127.0.0.1:8768/ on SAME machine
python -m pytest -q tests/test_paula_cloud.py tests/test_paula_receipt.py
```

## Deploy your own private iPhone URL (recommended)

1. Use a Linux PC at home (already owned, always on) or a small AWS EC2/other VPS. The first version needs CPU, RAM, disk and FFmpeg; it does **not** require a paid GPU.
2. Install Docker and Docker Compose on the server; copy this checked-out Vidmage branch. Run `mkdir -p paula-private-data && chmod 700 paula-private-data` (ensure its owner can write `/data`, e.g., UID 10001).
3. `cp .env.paula.example .env.paula` and put your real Cloudflare Access team domain, Application Audience tag, and explicitly allowed emails in the private file. `chmod 600 .env.paula`.
4. `docker compose -f compose.paula.yaml up -d --build`. The only host listener is `127.0.0.1:8768`.
5. In Cloudflare, create a **private web application** hostname (example `paula.YOURDOMAIN.example`), protect all paths with **Cloudflare Access** and an allow policy for Paula (and optionally you), enable Access JWT, and connect the hostname to `http://127.0.0.1:8768` using a remotely managed Cloudflare Tunnel. Install `cloudflared` on the same server (outside Docker). The site needs HTTPS on her iPhone.
6. Confirm an unauthenticated request is denied at the edge and directly at origin, an allowed user can create a synthetic test movie, and `/api/jobs/{job}/movie` is not public. Add your own private backup, retention and budget caps before storing real family media.
7. Paula opens the private URL in Safari and optionally **Share → Add to Home Screen**. She types a story, approves scenes, chooses **Make video on my server**, adds pictures/audio if wanted, and saves an actual MP4 to Files.

### Optional remote Flow browser (after reviewing metered usage)

Create a scoped Cloudflare API token with Browser Rendering Write permission and add `PAULA_BROWSER_ACCOUNT_ID` plus `PAULA_BROWSER_API_TOKEN` to your private `.env.paula` file. Restart the service. The `Use remote Flow browser` button asks first, then creates a Cloudflare browser session, navigates only to Flow Music, and returns a temporary human-interactive `live.browser.run` view. Users can press Close remote browser to release resources. Never publish the token or its returned Live View JWT. **Not integration with Flow's private APIs, and not a substitute for a supported official mobile app.**

### AWS alternative

Run the same Docker Compose service on an EC2 Linux machine with persistent EBS storage, encrypted at rest, no public inbound ports for the app, outbound network access for `cloudflared`, and budget alarms. The instance still accrues storage/compute costs even when idle. Keep media and signing keys on encrypted, backed-up storage. No EC2 instance, domain, DNS route, Cloudflare Access application, or API token is created by this branch.

### Before production for multiple users

- Add per-user retention/deletion and backups, quota enforcement, and job cancellation.
- Run worker jobs in a process-isolated queue rather than a server background thread.
- Use a transactional server-level token/receipt log for cross-worker scaling.
- Add virus/decoder hardening and upload antivirus if accepting media from broader public users.
- Do a phone-based test with actual media, rather than synthetic fixtures alone.
- Resolve platform rights/terms and Cloudflare Browser Run limitations with Flow login.

Do not call this project multi-tenant production-ready; it is for an explicitly allowlisted small household studio with controlled access.

## Independent receipt verification

```sh
# Download private JSON through the iPhone studio, then copy it to your trusted machine.
python -m paula_cloud.verify studio-receipts.json
# On the original server only, verify server authenticity with its private key:
python -m paula_cloud.verify studio-receipts.json --secret /path/to/paula-private-data/receipt-secret.key
# Optional exact MP4 proof (matches the most recent LOCAL_MP4_VERIFIED receipt):
python -m paula_cloud.verify studio-receipts.json --media movie.mp4
```

The exported cloud receipt format differs from the owner-local Paula Pocket 014 receipts. The owner-local `paula.receipt` verifier admits only its own format, with status HOLD. Do not relabel an external Flow video as a server-rendered MP4.
