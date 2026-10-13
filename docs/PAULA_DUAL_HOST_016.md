# Paula Dual Host 016 — Home and AWS

Two independent owner-authenticated Paula Pocket Vidmage nodes, not a shared render cluster. Mobile route `/nodes` allows explicit switch; no cross-node media sync, no auto failover. Cloudflare Access JWT enforced at origin; two Cloudflare Tunnels and hostnames. Home Linux install and AWS EC2 no-ingress SSM-based CloudFormation template in `deploy/`.

Capability claims: remote deployment not performed; EC2 template has only been YAML parsed, not CloudFormation deployed; custom Flow browser still experimental, manual external login. Local receipt/render tests pass using synthetic media. Keep author/client media in private data, never in repo.

Read `deploy/DUAL_HOST_SETUP.md` before launching.
