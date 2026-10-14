# Paula × Kling — Vidmage provider bridge 018

## Shipping state

**Kling handoff is live in the protected static front door** once Cloudflare Pages finishes deploying branch `feature/paula-domain-017-ph-abundent`. The private Home / AWS movie rendering machines are still **not provisioned**. Their future interfaces and backend are source only, under review.

Kling official website: https://kling.ai/
Kling developer API: https://kling.ai/dev
Kling Open Platform quick start: https://kling.ai/document-api/guides/get-started/quick-start
Kling 3.0 current text-to-video API: https://kling.ai/document-api/apiReference/model/textToVideo
Kling 3.0 current image-to-video API: https://kling.ai/document-api/apiReference/model/imageToVideo

## Paula's desired iPhone path

1. Open `https://ph.abundent.org`, sign into Cloudflare Access with an *approved* email. Paula's own email is not yet on the Access allowlist until the owner adds it.
2. Pick the planned private Home/AWS studio (**these private render machines are not deployed yet**). In its story editor, finish scenes, approve them, and tap **Copy Kling scene prompt**.
3. Open the real **Kling** website or app using her own sign-in; optionally add owned first-frame references. She chooses the model, duration and credit use herself. No credential/session scraping.
4. Download an authorized MP4 into iPhone **Files**.
5. Back in her authenticated private studio, **Import Kling clips** (up to 12 MP4s; 75 MB per clip; each from 1 to 30 seconds; 90 seconds total). Backend checks actual decode/duration/dimensions, stores source SHA-256, and signs `EXTERNAL_CLIP_IMPORTED` receipts.
6. **Join my Kling clips into a movie** runs FFmpeg on her selected private render machine; it normalizes portrait/landscape, joins clips in import order, and returns a new *byte-verified* MP4 and signed `IMPORTED_CLIPS_CUT_VERIFIED` receipt. Optional uploaded music replaces the clips' native audio; otherwise final cut is silent. This is an **editorial first cut**, not another Kling generation. No Kling credits are consumed by Vidmage.
7. Story backups and receipt exports remain owner-controlled. Do not claim that external provider provenance is cryptographically verified: content hashes prove only which local bytes were received/produced, not who generated them.

## Account and payment boundaries

- Kling consumer subscriptions/credits are **not the same as Kling Open Platform API credit packages**. Official developer quick start instructs users to purchase separate API resource packages and offers a trial package; no valid Kling API key has been provided for this project.
- Therefore `KLING_API_KEY`, automatic paid create-task calls, cloud-side download of private Kling URLs, and provider session automation are **not enabled**.
- Once Paula explicitly wants automated generation, connect an approved Kling developer API key **only on the private backend**, with per-task creator confirmation, quote/cost limits, daily caps, task-state polling, asset lifetime handling, and per-output receipts. Never store keys in web HTML, browser localStorage, GitHub or chat.
- The provider may impose output licensing, credit, watermark and attribution conditions. Follow the actual terms of Paula's account/plan and do not erase watermarks or imply permission to redistribute someone else's clips.
- For private family imagery, make an intentional decision before uploading media to third-party AI services. The manual handoff never uploads anything to Kling automatically.

## Source references and verification

`deploy/portal/index.html` — Kling door on protected custom domain (public `pages.dev` alias is static only).

`paula/index.html` — scene-specific Kling prompt and `KLING_HANDOFF_PREPARED` receipt.

`paula_cloud/studio.html` — iPhone clip picker, import button and local movie cut control.

`paula_cloud/kling.py` — FFprobe inspection, FFmpeg concat and actual video-byte SHA verification.

`paula_cloud/server.py` — authenticated MP4 intake / protected render / independent signed receipts.

`tests/test_paula_kling.py` — a real synthetic MP4 round-trip through upload → render → receipt → movie-download with assertions that external provider API isn't contacted.

**Known limitations:** the private cloud backend is unprovisioned; no iPhone live test, no Kling API login/auth/credit operation, no integrated native-audio track from downloaded clips, no public or synced media, no automatic failover. The optional flow-browser remains unrelated.
