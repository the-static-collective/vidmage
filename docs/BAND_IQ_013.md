# BAND-IQ 013 — The Candidate Tray × Grab/Cross Bits

**Experimental, real owner-local source composition.** Stacked on BAND-IQ 012 PR #16, without merging or public deployment. No external image generation, paid model credits, publishing, auto-KEEP, or silent modification of the original files.

## The useful weirdness

The song already has an actual Paper Director timed shot plan. The owner is composing their *unsealed* Storytable. BAND-IQ 012 introduced a THIS/THAT single-shot contact comparison. BAND-IQ 013 extends it along TWO orthogonal axes:

**1. The Candidate Tray — multiple possible arrangements.**

The artist can pin up to **four complete, alternative, unsealed arrangements** in the local browser, then keep adjusting the active draft without changing any pinned version. Every pinned candidate holds each native shot's specific original photo, focus, writing protection and optional crossed source bit.

A candidate can be compared against the current draft across all its changed windows. To remain affordable and safe, the native backend makes **six actual local sample frames per changed shot for at most six changed windows per comparison**. Any remaining changed shots are stated as omitted and unjudged, not assumed insignificant. Results are factual pixels from the existing VidMage raster function at 12/50/88 percent of each native shot's frame positions. The owner may **Apply this complete candidate to my draft** only after an independent explicit confirmation; doing so does not seal, render, keep or publish anything. Or discard a pinned candidate. The tray lives **only in the local browser's working memory** and is intentionally lost on reload, just as a sketch table should be.

**2. Grab/Cross Bits — move actual portions of owner-supplied pixels.**

The owner chooses one of the exact, already-prepared photographs and **grabs a bounded rectangular fragment** with either sliders or a source-image tap. The creator then selects a target song shot, positions the fragment on the selected shot's base photograph in a second live visual guide, chooses its target size and opacity, and explicitly clicks **Cross grabbed bit into shot**.

The bit is actual cropped pixel data from a photo the owner already supplied, not an inferred object, generated image, new source URL, or guessed semantic mask. A simple deterministic feathered cross-fade preserves the piece's boundary. Only **one independently placed crossed piece per shot** and a maximum of **36 crossed shots** are allowed in this experiment. There is no claim of object segmentation, generative inpainting, depth reasoning or perfect compositing.

The crossed bit is **an unsealed draft instruction** until a human takes a separate, explicit Storytable seal action. Before sealing, the existing 012 THIS/THAT renderer can preview its real source-crossed pixels without writing image files. Pinning such a draft to the Candidate Tray preserves the exact source crop/placement/opacity for later comparison or reuse.

### How source truth survives into *real* films

At the separate artist **Seal my Storytable** crossing:

- The bit instruction is validated against the real prepared **owner-owned source image IDs**. It cannot point to arbitrary filesystem paths or URLs.
- The source parser reopens the original prepared base and fragment image bytes, records **both source SHA-256s**, the normalized crop rectangle, target placement rectangle, opacity and the deterministic local raster rule.
- A new **working composite PNG** is generated under a fixed private folder \`paper-tray/cross-bits/<bitSha256>.png\`; creation is create-only, with original PNGs entirely unchanged. The SHA of this derived image is also source-bound.
- The normal 010 human-authored shot entry now contains a **crossBit** provenance receipt with both original source identities and the derived SHA. Its signed Storytable hash binds that to the exact native song shot, focal point and protect-text mode.
- The 010 editorial scene-card **asset for that shot points to the derived working PNG**. Both the real VidMage/FFmpeg baseline and the **independent native Playdeck Remotion** first-film renderer receive the *same source-picked resulting composite still*, then apply their respective native camera languages. No false claim that the two renderers are pixel-identical.
- The existing BAND-IQ 011 sealed source filmstrip and downstream Workbench read the same derived card. Restart independently **recomposes from the real originals** and verifies that the sealed bit metadata, derived bytes, authored card SHA, both film SHAs and original first human review are still consistent. A forged or modified fragment becomes a HOLD.

No bit file is created by clicking Grab, Cross, Compare or Apply candidate. The source changes only by creating a new separate derived file *at the explicit human Storytable seal*. The original images and audio remain intact. Reusing one original photograph across shots with different crossed fragments remains supported because every shot already has a distinct per-occurrence editorial asset.

## Creative sequence

1. **Bring:** one owned song + 2–12 owner-authorized images into the local 009 Front Porch.
2. **Prepare:** native pinned Toaster/Blender create the song's factual timing, with no film.
3. **Compose:** use the 010 Storytable's authored per-shot photo, focus and text-protection controls.
4. **Grab/Cross Bits:** take a bounded piece of another owned source, position it across this song shot, and optionally show the new real source pixels using 012's THIS/THAT.
5. **Pin candidates:** save several complete unsealed alternatives, change other shots, compare across changed windows, and explicitly select one coherent arrangement to bring into the draft if you choose.
6. **Seal Storytable:** a separate named human attestation signs the full exact story, including every referenced owner-source fragment.
7. **Develop filmstrip:** the existing 011 source-real, immutable preview from that sealed story.
8. **Make A/B:** a separate named human choice of camera grammar authorizes genuine VidMage A and independent native Playdeck B film performances.
9. **Choose:** the earlier 004/007 human review rooms remain authoritative; no film becomes a selected final version automatically.

## Local setup

Same native donor prerequisites as BAND-IQ 009–012: FFmpeg/ffprobe, Python + Pillow/OpenCV/numpy, Node and source-pinned Blender/Toaster/Playdeck checkouts.

From the BAND-IQ 013 branch:

    python -m bridge.band_iq_front_porch \
      --workspace /private/vidmage-projects/your-song \
      --blender-root /private/donors/haunted-blender \
      --toaster-root /private/donors/haunted-toaster \
      --playdeck-root /private/donors/playdeck \
      --port 8767 --open-browser

Open **http://127.0.0.1:8767/** from that same computer. The Front Porch is owner-local, not a hosted public service. It never communicates personal media to a provider.

## Source and browser boundaries

\`bridge/band_iq_candidate_tray.py\`: validates finite, bounded [x,y,width,height] normalized grab and cross boxes, actually rasterizes a 640x360 prepared original and source patch with bounded opacity and a simple feather, hashes the resulting real PNG, refuses unrelated source paths and only materializes a create-only derived image on explicit Storytable seal. \`bridge/band_iq_storytable.py\` now preserves and verifies optional per-shot cross-bit provenance, source SHA and derived working asset; old 010 shot entries without bits still work.

\`bridge/band_iq_contact_sheet.py\`: previously built single-shot contact renderer now accepts bounded optional crossed fragments and shows true pixels in memory; no new JPEG files or user source changes. The additional \`bridge/band_iq_front_porch.py\` \`POST /api/porch/candidate/compare\` takes **exactly two source-defined whole-story alternatives**; all authority flags are false, requests require the existing random session token plus same Origin/Host, and native media identities are rechecked. It returns a SHA-bound **in-memory** factual comparison with up to six changed shot windows. Browser images use fixed routes:

    GET /api/porch/candidate/frame/<candidateSha256>/<0..5>/<left|right>/<0..2>

A second candidate comparison replaces the first one in session memory. After sealing, candidate frames are inaccessible and further candidate previews are rejected. No arbitrary server file path, no in-chat browser uploading, and no automatic merge or global state is used.

\`ui/band_iq_front_porch.{html,css,js}\`: editable crop and placement guides (tap or bounded sliders), grabbed-bit handoff, four in-memory pinned alternatives, multi-shot factual preview frames, explicit Apply / Discard, and visible limits. The browser only calls fixed same-origin server routes and does not claim a provisional candidate is a saved owner Storytable. It works with mobile widths and existing reduced-motion preferences.

## Test evidence

- \`tests/test_band_iq_candidate_tray.py\`: actual decoded synthetic source images; deterministic real PNG compositing, two distinct original image SHAs, different before/after raster outcomes, no pre-seal materialization, source and derived pixel tamper refusals, exact Storytable source-verified replay, unknown source paths, malformed crop/opacity and attempted privileged fields.
- Extended \`tests/test_band_iq_front_porch.PorchNativeTests\`: actual song/photos → native Toaster/Blender paper → multi-shot session-memory candidate POST under strict origin/refusal → real hashed JPEG GETs → explicit 010 artist Storytable seal using a **crossed pixel fragment** → stale candidate frame refusal → real 011 source filmstrip → real VidMage MP4 A and native Playdeck Remotion B → independent human review → durable private restart. A/B video and owner original hashes remain independently checkable.
- \`.github/workflows/band-iq-013.yml\` tests source and UI safety, then reruns exact pinned donor builds \`cf0256...\` Blender, \`3652c2...\` Toaster and \`012186...\` Playdeck using synthetic media only.

### Non-collapse laws

GRAB != EXTRACTING A SEMANTIC OBJECT.

CROSS != REWRITING AN ORIGINAL.

CANDIDATE != DECISION.

APPLY != SEAL.

COMPOSED PIXEL != AUTOMATIC ARTISTIC VALUE.

DERIVATIVE SOURCE != PERMISSION TO PUBLISH.

MULTI-SHOT COMPARISON != COMPLETE FULL-SONG EVALUATION.

SEAL != MOVIE RENDER.

HISTORY != ERASURE.
