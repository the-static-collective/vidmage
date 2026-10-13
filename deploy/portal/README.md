# Paula's movie front door · ph.abundent.org

Status: source prepared, **NOT LIVE** until Cloudflare, DNS, and at least one node are configured. No account tokens or Paula's media belong in GitHub.

## The fixed addresses

- `https://ph.abundent.org` — a **static**, mobile-first Cloudflare Pages front door. Nothing private is stored or submitted here. Enable Cloudflare Access for this host.
- `https://home.ph.abundent.org` — tunnel `paula-home` to **Home Linux** `http://127.0.0.1:8768`.
- `https://aws.ph.abundent.org` — separate tunnel `paula-aws` to **AWS EC2** `http://127.0.0.1:8768`.

The home and AWS sites retain separate private SQLite databases, uploaded media, and HMAC receipt keys. No invisible DNS failover or replica tunnel. The portal is just an accessible link selector, not a state router or reverse proxy. The Flow link opens Flow Music in its own domain; it does not hijack login or programmatically operate Flow.

## Before changing the live domain

Read-only Porkbun audit on 2026-10-13 established that **abundent.org** is an active Porkbun domain with Porkbun nameservers. Its Cloudflare integration was **not connected**. The dry-run migration preview reported **six ordinary records copied and zero skipped**: two apex A records, a wildcard CNAME (Porkbun), the existing www/Vercel CNAME, and two ACME challenge TXT records. The registrar's four NS records are not copied as ordinary zone content. These are live website records — preserve them! Check the current preview again immediately before migration, in case the zone changed. Do not delete or overwrite the existing www and apex records, wildcard, or certificate TXT records. No migration has been requested by this code.

## Connection and domain audit — 2026-10-13

The user completed interactive authorization. Read-only verification now shows **Porkbun ↔ Cloudflare connected**. This authorizes API access, **not** a move of nameservers.

- Domain migration queue: **NOT_QUEUED**. DNS nameservers still Porkbun.
- Live Porkbun DNS inventory: two A records on apex, a wildcard CNAME to Porkbun parking, a www CNAME pointing to Vercel, and two `_acme-challenge` TXT tokens, plus registrar NS records.
- Migration preview: **6 records copied, 0 skipped**. These would be DNS-only at first. Any future Cloudflare proxy/Access decisions must be independent.
- Porkbun eligibility: **WARN** because wildcard Porkbun parking is in use. Porkbun-issued free SSL may **stop renewing** after moving the domain. Verify any existing origin/certificate dependencies before a cutover.
- No active Porkbun static hosting, URL forwarding, or email forwarding was returned by read-only checks. DNSSEC DS read returned null.
- **Migration authorized and queued 2026-10-13.** Porkbun changed registrar nameservers to `damien.ns.cloudflare.com` and `lilith.ns.cloudflare.com`; Cloudflare zone `e30c00c477785e33d5e9db102fe695a4` has all six original DNS records (DNS-only). Cloudflare activation remained `pending` at last verification; its public delegation read may lag registry state. No Pages, Access, tunnels or EC2 created, and the website HTTPS has not yet been independently checked. Confirm zone `active` before provisioning hostnames.
- **Human approval gate:** explicitly confirm whole-domain authoritative DNS migration *after* reviewing expected website and certificate impact. Cloudflare connection is insufficient consent. Preserve the existing records.

## Step 1: human connects Cloudflare to Porkbun

**Completed 2026-10-13:** owner authorized Cloudflare from Porkbun's browser session. Read-only connection check returned active. Do not repeat unless disconnected; proceed only after the separate nameserver migration authorization. Never store Cloudflare credentials here or in chat.

Once connected: obtain a fresh Cloudflare migration preview; review DNS preservation, CAA/DNSSEC, mail records, website routes, and hostname conflicts; only then approve domain migration and nameserver change. Migration will affect the **entire abundent.org zone**, not just Paula's subdomain. Do NOT migrate automatically merely because authorization is complete.

## Step 2: provision Cloudflare public hostnames and private Access policies

1. Cloudflare Pages: new project from GitHub `the-static-collective/vidmage`, set branch `feature/paula-domain-017-ph-abundent`, no build command, build output directory `deploy/portal`. Configure custom domain **ph.abundent.org** using Cloudflare Pages. If using CLI instead, with your own authenticated Cloudflare login: `npx wrangler pages deploy deploy/portal --project-name paula-movie-portal`. The named Pages project must first exist; choose a different name if already taken.
2. In Cloudflare Zero Trust → Access → Applications, protect **ph.abundent.org** with an Allow policy for only Paula and designated helpers; use email OTP or an identity provider that works on her iPhone. Keep the exact identities in Cloudflare, not GitHub.
3. Create **separate** private Access web applications for `home.ph.abundent.org` and `aws.ph.abundent.org`, with the same deliberate allowlist. Copy each application's **own** Application Audience (AUD) into that node's private `.env.paula`. Record the shared team domain as `https://YOURTEAM.cloudflareaccess.com`; never paste secrets into a chat.
4. Create two *different* remotely managed Cloudflare Tunnels with corresponding public hostnames and route each to **127.0.0.1:8768** on its own machine. Install `cloudflared` using the dashboard-provided shell command on each origin; protect with Access and require signed JWT at origin.
5. Review records created for these exact hostnames. The pre-existing wildcard DNS record must not steal the three exact hosts; specific entries should override the wildcard. Do not copy tunnel credentials from one machine to another.

## Step 3: run the two engines

Use `deploy/DUAL_HOST_SETUP.md` for Ubuntu installation and the `deploy/aws/paula-ec2.yaml` CloudFormation plan. Set monthly AWS Budget alarms *before* creating the EC2 instance. Stack has zero inbound ports, encrypted EBS and Systems Manager access; it nevertheless incurs instance, storage, and possible public IPv4 charges. Review the EC2 instance profile and routes before running it.

For **each** machine, in a checkout of `feature/paula-domain-017-ph-abundent`:

```bash
cp .env.paula.example .env.paula
chmod 600 .env.paula
# Set PAULA_CF_TEAM_DOMAIN, PAULA_CF_AUD, PAULA_ALLOWED_EMAILS, PAULA_NODE_LABEL
bash deploy/start_node.sh
bash deploy/node_preflight.sh
```

The example already pins `PAULA_HOME_URL=https://home.ph.abundent.org` and `PAULA_AWS_URL=https://aws.ph.abundent.org`. Set different `PAULA_NODE_LABEL` and different Access `PAULA_CF_AUD` on Home versus AWS. Original photos, generated films, receipt keys, and private `.env.paula` must never be committed.

## Step 4: no-guesswork acceptance test

1. Without Cloudflare Access authorization, opening each of the three hostnames must **fail** to show the protected studio.
2. Via a non-Access local origin request to `http://127.0.0.1:8768/`, backend must return 401 or 503 (not the app).
3. Authorized iPhone Safari: visit `ph.abundent.org`, tap Home, sign in, create a *synthetic* story, upload a synthetic picture, render a short MP4, download it and its receipt; validate movie SHA-256.
4. Tap AWS; confirm it is a different node and separately render there. A project from Home must **not** appear in AWS until intentionally exported and imported.
5. Test Home powered down: portal remains reachable and AWS link still works. Test AWS stopped: portal and Home remain reachable. Portal independence from either renderer is a design requirement.
6. Test iPhone Safari home-screen behavior, VoiceOver, login renewal, file-picker, and Files download on Paula's actual device before admitting family media.

## The wall

The code and hostname wiring can be prepared without Cloudflare authorization. The first outside-account action is the **human Porkbun ↔ Cloudflare consent** in Step 1. A separate explicit decision is needed to change nameservers because `abundent.org` already serves other properties. AWS budget/VPC and the physical Home PC are later operator steps. Never present a demo as a live deployment.
