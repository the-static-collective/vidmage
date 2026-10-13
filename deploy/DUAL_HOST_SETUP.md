# Paula Vidmage — ph.abundent.org (Home + AWS)

**Permanent entrance:** `https://ph.abundent.org` (Cloudflare Pages static portal); Home: `https://home.ph.abundent.org`; AWS: `https://aws.ph.abundent.org`. Portal does not proxy, persist or sync projects. For exact migration and Access steps, see `deploy/portal/README.md`.

## State and boundaries

**Prepared infrastructure, not deployed.** Two copies of the same studio operate independently. Each must have its **own storage directory, receipt signing key, separate Cloudflare Tunnel, and Cloudflare Access-protected HTTPS hostname**.

```text
                                Paula's iPhone (Safari)
                              ↙                      ↘
           home.ph.abundent.org                 aws.ph.abundent.org
           Cloudflare Access                      Cloudflare Access
           Cloudflare Tunnel HOME                 Cloudflare Tunnel AWS
           your Linux PC                          Ubuntu 24.04 EC2
           Vidmage private database                Vidmage private database
           images / songs / receipts               images / songs / receipts
                  (NO automatic data sharing or transparent failover)
```

**Why not one tunnel / load-balancer yet?** The current SQLite + receipt store is local to each machine. Cloudflare Tunnel replicas will happily route successive requests to *different computers*, producing split data, split receipt ancestry, broken media lookups, and misleading render status. Do **not** reuse a tunnel token across these hosts or load-balance them until database/object storage coordination is actually implemented and tested. The two distinct hostnames are intentional. [Cloudflare docs](https://developers.cloudflare.com/tunnel/concepts/routing/).

## Required before deployment

- A domain you control in Cloudflare, two private Access applications and two remotely managed tunnels.
- Email address Paula uses for Cloudflare Access one-time PIN, and your own if you also need access (type these privately into each host's `.env.paula`; **never put them into ChatGPT or GitHub**).
- Home Linux PC with outbound internet and enough disk; no public inbound ports.
- AWS account: an Ubuntu EC2 instance in a suitable VPC/subnet, AWS Billing budget/alert. The provided CloudFormation creates the AWS compute. It incurs charges, including EBS even when stopped.
- Separate backups for each host. Media and receipts do not synchronize when you tap **Switch studios**.

## Home computer

1. Install Ubuntu 24.04 LTS (or compatible Ubuntu machine). Keep it powered on and updated.
2. Clone repo and checkout branch `feature/paula-domain-017-ph-abundent`.
3. `bash deploy/install_docker_ubuntu.sh` (installs Docker/Compose from official Docker apt repository).
4. `cp .env.paula.example .env.paula && chmod 600 .env.paula`. Edit `PAULA_NODE_LABEL=Home studio`, set **real** Cloudflare Access team domain, audience tag, and allowed email(s); both `PAULA_HOME_URL=https://home.ph.abundent.org` and `PAULA_AWS_URL=https://aws.ph.abundent.org`.
5. `bash deploy/start_node.sh`. Container runs at `127.0.0.1:8768` only; backend *refuses* unsigned Access tokens.
6. In Cloudflare dashboard create a private web application for `home.ph.abundent.org`, allow only Paula/you, and a separately named tunnel `paula-home`. Route public hostname to `http://127.0.0.1:8768` and install `cloudflared` as a local service **using the dashboard's command**. Set **Protect with Access** in Tunnel settings where available so the origin is additionally protected by JWT validation. No router port forwarding.
7. Test from Paula's iPhone on mobile data. Log in with her email OTP, create a synthetic story and render a small MP4. Confirm unlisted email is blocked.

## AWS computer

1. **Set an AWS Budget alarm first**. AWS Console → Budgets → create monthly cost budget; note that alert alone is not a hard spending cap.
2. AWS Console → CloudFormation → Create stack → Upload `deploy/aws/paula-ec2.yaml`, specify correct `VpcId` and **public subnet** with Internet Gateway route, choose a machine size and 40 GiB gp3 encrypted disk by default. Review IAM permissions. This creates an Ubuntu EC2 host with **zero security-group ingress rules**; Session Manager is provided through the `AmazonSSMManagedInstanceCore` IAM instance profile. An outbound public IPv4 address may have separate charges.
3. Wait for EC2 to boot. AWS Systems Manager → Session Manager → Start session for instance ID from stack output; change user to ubuntu (`sudo -iu ubuntu`) and enter `/opt/paula-vidmage`. If cloud-init clone/install failed, repair using the logs `/var/log/cloud-init-output.log` and rerun `deploy/install_docker_ubuntu.sh`. No SSH hole is needed.
4. Create `.env.paula` as on Home, but `PAULA_NODE_LABEL=AWS studio`; use *the same* Access team domain and allowed email list, **the audience for the AWS Access application** (likely a different AUD), and the same two URL labels.
5. `bash deploy/start_node.sh`. Create a **different** Cloudflare Tunnel `paula-aws`, Access application and route: `aws.ph.abundent.org` → `http://127.0.0.1:8768`. Configure local cloudflared service through the dashboard, never paste tunnel tokens into git/chat.
6. Test `/api/health` after login and a real tiny film; verify home and AWS show different node labels on `/nodes`.

## iPhone workflow

Paula bookmarks **Home studio** and **AWS studio** in Safari. Tap **Switch between Home and AWS studio** to open the other protected URL. Story, scenes, receipts, and MP4s remain on the original host. Before switching, save a JSON story backup from her phone, then import it on the destination and re-upload reference photos/audio. (This is manual *story portability*, not full automatic transfer of signed server render history.)

## Recovery & security

- Home offline: use AWS studio; import the previously exported story JSON manually. Media from Home must be available as a separate owner-held backup.
- AWS stopped: Home keeps working; AWS instance hours stop but EBS storage may still incur charges.
- If a project requires its exact old renders/receipts, reopen **that host** or restore its privately encrypted full-volume backup; do not copy signing keys between two active hosts.
- Avoid automatic DNS failover or duplicate tunnel replicas while database/receipt storage is node-local.
- Set finite storage policies, backup encrypted `/data` separately on each machine, test recovery, and audit machine permissions before real family videos.
- **Not production-multiuser ready:** server rendering is a single-thread guarded queue; user media are private only behind configured access controls and the small-group allowlist. Requires real iPhone Safari testing.
- The Flow button is a direct link to Flow Music. Optional Cloudflare browser session is a separate metered, creator-initiated experiment; it is not an embedded Flow API or a Google sign-in proxy.

## Verification steps (both nodes)

1. `bash deploy/node_preflight.sh` reports Docker, env, loopback connectivity.
2. `sudo docker compose -f compose.paula.yaml ps` reports service up.
3. `curl -I http://127.0.0.1:8768/` should return **401 or 503**, *never* a public page when missing Access token.
4. Visit the separate hostnames from a different device without a login; Access must require authentication.
5. Log in with an approved email, use `/nodes`, upload a **synthetic** photo, render; verify the MP4 and downloadable signed receipt on each host.
6. Power off Home and ensure AWS hostname still works (no DNS reconfiguration). Power off AWS and ensure Home remains independently reachable.
7. Test iPhone JSON story backup and import between **hostnames**; separately re-upload source media.

Canonical references: [Cloudflare private web application](https://developers.cloudflare.com/cloudflare-one/setup/secure-private-apps/private-web-app/), [Cloudflare tunnel](https://developers.cloudflare.com/tunnel/get-started/), [AWS Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html), [Ubuntu AMIs](https://ubuntu.com/aws/docs/aws-how-to/instances/find-ubuntu-images/).
