# BAND-IQ 009 — The Front Porch

**Status:** executable experimental first-user intake, stacked on BAND-IQ 008 PR #12. New source material → verified native Toaster/Blender preparation → separately approved genuine A/B VidMage + Playdeck MP4 render → original Living Workbench with actual human review.

No branch merge, account registration, public deployment, upload to a model provider, unapproved paid tool or publication. Native donor checkouts and local tools are still **technical installation prerequisites**; the new browser experience removes the artist's need to prepare JSON receipts by hand, not the operator's responsibility to install the pinned engines.

## What the creator actually sees

An analogue, quiet, slightly off-kilter entry room. No mock upload cards. The three stages are functional:

1. **Bring:** upload one local audio file (WAV, MP3, M4A, FLAC, OGG; max 36 MB, verified audio stream, 0.8–360 seconds) and 2–12 actual owned images (PNG/JPEG/WebP; max 12 MB each, capped dimensions and decode verification). Preview thumbnails show the actual original bytes. A creator names their project and checks explicit rights, local-derivative permission and private/no-publication acknowledgement. Submitting signs an exact SHA-addressed **source intake receipt**. Audio/image bytes stay on that computer under a fixed private workspace; media cannot be silently exchanged after permission is recorded.
2. **Let it take shape:** creator separately asks for **local paper preparation**. Source copies become standard WAV and fit-to-canvas PNG stills, preserving every original. The program calls actual pinned Toaster L BRANCH audio analysis and native Blender scene-growth/Paper Director planning; scene-card assignments are **provisional by uploaded image order**, not inferred semantic story facts. A bounded SHA-addressed paper tray records every source and donor identity. **No film is rendered yet.**
3. **See two films:** creator chooses exactly ONE of six already pinned cinematic languages: landscape, architecture, organism, sigil, weather or dimensional-space. A second explicit named artist act authorizes a single local A/B performance (no payment, public release or network media upload). VIDMAGE actually renders baseline source film locally; native Blender Doctor observes the baseline, and an explicitly author-approved motion-review window becomes the selected test (stillness is never assumed a defect). Real VidMage/FFmpeg renders **A**, actual pinned Playdeck Remotion renders **B**. Both videos and their original source/film/review receipts are individually hashed. **Neither is automatically kept.** The program verifies the original A/B pair and creates a private BAND-IQ 008 workbench profile without asking the creator to author any JSON.

Once complete, reloading the **same local root URL** opens the Living Workbench with its seven real doors. The actual /room already supports independent human KEEP A / KEEP B / SCRAPE BOTH / ANOTHER EXPERIMENT decisions and subsequent 005/006/007 revision flow. The earlier camera choice is permission to make an unselected trial, NOT an artistic final selection.

## Launching locally

The production engines must first be installed by an operator. **This is not a zero-install web app**: it executes local native tools. The exact Git checkouts required by the preexisting BAND-IQ system are:

- Haunted Blender source HEAD: cf0256a49ac8aa879cf2a044847d248177fcfad9.
- Haunted Toaster source HEAD: 3652c2a96b6b287cda316d1c92daadf7c7417eaf.
- Playdeck source HEAD: 012186fd67f4c4ef1c6591fc5e29cb559b5a80d0, with its native Remotion dependencies installed.
- Python 3.12+, numpy, OpenCV, Pillow, FFmpeg/ffprobe, Node 22+, and available native Playdeck modules. All unmerged donor branches are checkout-pinned rather than substituted with whatever main currently contains.

From the VidMage repo, in the user-owned machine's terminal:

    python -m bridge.band_iq_front_porch \
      --workspace /private/vidmage-projects/my-first-song \
      --blender-root /private/donors/haunted-blender \
      --toaster-root /private/donors/haunted-toaster \
      --playdeck-root /private/donors/playdeck \
      --port 8767 --open-browser

The local URL is **http://127.0.0.1:8767/** and binds only to that exact loopback address. A new creator can then bring the actual song and images in the browser and explicitly choose when to proceed. The server reads the browser uploads locally; it never transmits their contents to GitHub or to an AI-generation provider.

The browser's longer render happens **synchronously after the separate human MAKE action**; the UI warns that the connection can remain occupied while native Remotion works. It is not a hosted queue or silent background worker. Long real songs may take substantial local CPU time. The existing Remotion implementation has its own maximum native command timeout. The 009 tested path proves short synthetic videos, not a claim that every 6-minute song renders within the native tool's current timeout.

### Private local folder anatomy

The selected workspace contains:

- original/song.[original extension] and original/images/image-XXX.[source extension]: **unchanged** uploaded bytes, never silently overwritten.
- consent.json: signed original media ownership/local-derivative attestation with exact original audio and image hashes.
- paper-tray/song.wav and source-XXX.png: creator-authorized local working copies.
- paper-tray/toaster-observation.json, paper-plan.json, scene-cards.json, proposal.json: original native observation and temporary/editorial planning source truth.
- first-films/attempt-XXX/baseline.mp4, vidmage-a.mp4, native-playdeck-b.mp4: actual distinct local performance files and their native receipts. Failed attempts remain isolated; another attempt requires another explicit human click.
- human-reviews/: original BAND-IQ 004 review receipts, eventually the 005/006/007 experiment/observation/AC records.
- first-performance.json: source-intake-to-actual-A/B custody receipt.
- private-workbench.json: owner-readable (mode 0600), create-only pointer map for BAND-IQ 008.

**Private means local, not secret from whoever has filesystem or browser access on the same computer.** The application binds only to 127.0.0.1, requires strict same-origin headers and unpredictable per-session capabilities for every write, and serves only fixed browser resources and bounded uploaded image previews.

No arbitrary file path is accepted from an upload or any HTTP request. Incoming original filenames are constrained to simple basenames, but the stored names are generated locally. The server never browses source folders supplied by HTTP. No remote image/JS/style/CDN, no external provider, no content download from another website, and no user-owned artifacts checked into the repository.

### Authority split

- Uploading files != permission to use them in a film.
- Rights/local derivative consent != permission to render.
- Preparing native audio and scene proposals != making a movie.
- Six cinematic possibilities != six renders.
- One film trial authorization != a human KEEP or final cut.
- Native Toaster/Blender analysis != semantic knowledge of subjects or lyrics.
- Native Blender Doctor measurement != a claim that stillness is wrong.
- VidMage movie != native Playdeck rendering. Two genuine engines produce distinct film evidence.
- Existence of completed film != account creation, publication, deletion or provider spend.
- Restarting a project != performing earlier edits again. Real source/film receipts are verified at each transition.

## Tested behaviors

New tests/test_band_iq_front_porch.py covers:
- Actual decoded WAV and photo upload, hard file/duration bounds, path traversal name refusal, source-rights requirement, irreversible owner source consent, readback, altered-file HOLD and no early rendering.
- Browser same-origin and session token refusal, raw-byte file upload with fixed content type, actual private photo previews, unknown file route refusal, duplicate consent refusal and no workbench before real movie evidence exists.
- **Full native synthetic media proof**: actual 4-second WAV + two real textured photographs, separate ownership and local preparation acts, genuine Toaster L BRANCH/Blender Paper Director observation, explicit six-lens artist choice, actual source-pinned VidMage A + native Playdeck Remotion B MP4s, original pairing, first human A/B choice via the same local server, generated working BAND-IQ 008 profile and successful restart without re-rendering or losing that human choice.

.github/workflows/band-iq-009.yml runs independent fast local evidence checks, then fetches exact pinned native donors and proves real media through the full user-facing HTTP workflow. CI uses **synthetic local files only**, not the creator's personal media.

## Known boundaries

This version is a genuine functional first-use **local** intake and two-renderer movie process, not a hosted no-install service. The initial provisional source order and shot plan are not yet edited through a drag-and-drop scene director before first render. Creator-controlled reframe, image swap, and camera changes exist in the downstream question laboratory after an explicit first A/B review. The first-cut image assignment is visible as the ordered original stills, and the original source files remain available for later revision.

Next improvement: a pre-render **storytable** where the artist chooses/reorders each shot and its source image, sees song timing visually and previews private framing *before* authorizing the first VidMage/Playdeck performance. That is a separate slice because a technical planning heuristic is not permission to pretend the creator told a story.
