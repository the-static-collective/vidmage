# BAND-IQ 013 — Candidate Tray × Grab / Cross Bits

Experimental, owner-local and stacked on BAND-IQ 012 PR #16. No merge, deployment, cloud media transfer, provider spend or automatic creative selection.

## Why this particular crossing exists

After the 012 Contact Sheet, the creator could compare one shot's current photograph against a different source or focus, and apply that alternative to an **unsealed** story. BAND-IQ 013 introduces two connected abilities:

**Candidate Tray:** Keep up to **four complete, independently editable story arrangements** in temporary browser memory. Each candidate holds all actual shot IDs, source image selections, per-shot focal coordinates, text-protection choices and any borrowed picture pieces. Compare the current shot of a saved candidate to the active draft with actual local VidMage pixel samples. Explicitly **Put whole candidate in draft** to copy the full alternative arrangement onto the *unsealed page*; save the previous arrangement to a different temporary slot beforehand. Candidate snapshots do not become saved Storytable receipts, films or user media. Closing/reloading the tab discards them.

**Grab / Cross Bits:** On a given real song window, pick one already-owned photo as a donor, set a bounded rectangular **grab** box, a bounded destination **place** box and opacity; then use **Compare grabbed pixels** to view three actual source raster samples of the original shot beside three from the crossed possibility, at matching native song times. The borrowed piece is a literal image rectangle, **not object segmentation**, proprietary inpainting, AI semantic selection, erasure or a destructive cut. Up to three borrowed rectangles can occupy a shot. Existing base and donor photographs retain their original bytes.

The creator can **Cross these bits into my draft**, **Leave the source alone**, or save the updated multi-shot arrangement to their Candidate Tray. A new comparison replaces the preceding temporary images in the local process. The existing 010 **Seal my Storytable** remains a **different human permission crossing**.

## The important film-custody seam

This is not an overlay that mysteriously disappears once a real movie is made.

1. During unsealed trial and comparison, the backend derives left/right candidate pixels using the actual VidMage \`scene_card_film.frame_for\` raster function, true Toaster audio energy, native Blender shot boundaries and the real source images. Six temporary JPEG bytes are kept **in session memory only**, with hash-pinned source and native frame IDs.
2. Only during an **explicit 010 Storytable seal**, the backend reproduces the selected bounded crops from the original owned prepared PNGs. Each derived shot occurrence gets its **own** create-only image file at \`paper-tray/crossed-bits/shot-asset-XXXX.png\`; no existing image is overwritten.
3. The signed 010 \`story-seal.json\` records **both** base image source SHA and every donor source SHA/rectangle/opacity, as well as the exact derived composite SHA (\`crossedImageSha256\`). It never mistakes a composite for a newly acquired original.
4. The authored scene cards now point to the separately materialized derived PNG for a crossed occurrence. VidMage's real baseline, native Blender observations, actual VidMage A, native Playdeck Remotion B and the existing 011 Living Filmstrip consume the **same per-shot source card path**. The 011 verification uses the crossed image's actual hash where applicable.
5. Reopening the signed 010 Storytable **recreates the expected composite bytes from the original base and donor pictures** and checks them against the derived file and receipt. A changed donor, shifted crop, forged receipt or modified composite cannot be silently accepted.
6. Human first-film KEEP, further 005–007 revision approvals, and public publication all remain separate permissions. The existence of an illustrated borrowed piece never authorizes export, a model call, deletion or a new movie.

### Source and operator limits

- Up to **four** temporary full-story candidate snapshots in the browser.
- Up to **three** explicitly bounded rectangular image pieces per native song shot.
- Every donor **must** be one of the 009 owner's already registered prepared photos.
- Both crop rectangle and landing rectangle use normalized [x, y, width, height], contained fully in the source image, with each dimension at least 5% of its source. Explicit opacity is bounded 10–100%.
- Each bit contributes its own donor source ID, original SHA, grab, placement and opacity; order is significant.
- Source images are decoded by native OpenCV and resized into the target rectangle; alpha compositing uses deterministic local BGR pixels. This cannot preserve semantic cutout boundaries automatically; it is intentionally a simpler controllable creative primitive.
- The native Blender Paper Director's song timing and original machine-provisional paper cards remain untouched. The original song/photo bytes remain unchanged.
- The Contact Sheet and Candidate Tray are **temporary**; only a later named human Storytable seal creates derived photo assets and source receipts. The owner retains the rights and derivative-use constraints from original 009 consent.

## One existing local command

The experimental front porch is still the same private local app, now with the Grab / Cross panel appearing inside the unsealed Storytable:

    python -m bridge.band_iq_front_porch \
      --workspace /private/vidmage-projects/your-song \
      --blender-root /private/donors/haunted-blender \
      --toaster-root /private/donors/haunted-toaster \
      --playdeck-root /private/donors/playdeck \
      --port 8767 --open-browser

Open **http://127.0.0.1:8767/** on the machine running the pinned local tools. The app still requires actual FFmpeg, Pillow/OpenCV, Python, Blender, Toaster, Node and native Playdeck dependencies; it is **not** a publicly hosted no-install web app.

### New API surface

\`POST /api/porch/cross/compare\` accepts exactly one native shot ID and two explicit source choices (each an owned base, focus, text-protection and up to three bounded donor rectangles), plus exact project paper SHA, compare-only true and all release/provider/movie/seal permissions false. The server enforces loopback origin, scoped session token and bounded JSON. A valid response is an ephemeral \`vidmage/band-iq-013-crossed-bits-contact/v1\` content-hashed comparison; its actual JPEG bytes are served using the already established bounded \`GET /api/porch/contact/frame/<SHA>/<left|right>/<0|1|2>\` route.

\`POST /api/porch/story/seal\` is **unchanged as a separate human action** but now accepts shot selections with an optional \`crosses\` array. A valid seal generates only the approved derived pixels and their independent source identities. This is **not** a direct render or a shortcut around owner attestation.

## Executable source-backed verification

- \`tests/test_band_iq_cross_bits.py\`: actual decoded real-colored source photos, bounded rectangle/opacity validation, six genuinely distinct cross-contact frames and exact JPEG hashes, source originals unchanged, no preview-created files, different visual outcomes, explicit materialization only at seal, exact base+donor source SHA lineage, altered derived PNG refusal, successful 010 Storytable re-open, real 011 filmstrip output from crossed image, and rejection of outside source/media/paid/publication privileges.
- Extended \`tests.test_band_iq_front_porch.PorchNativeTests\`: a genuine synthetic WAV and two pictures traverse the full native Toaster/Blender preparation. HTTP tests both old 012 preview and new **013 cross preview**, including cross-site refusal, correctly source-hashed JPEG delivery and no pre-seal derived files; the human then seals the Storytable, invalidating all old previews, and creates the derived image whose base/donor hashes are independently verified. Full native VidMage A and Playdeck B films and a separate signed human choice follow, including restart and genuine 011 filmstrip source verification.
- \`.github/workflows/band-iq-013.yml\`: fast source/cross/refusal/browser syntax suite plus actual SHA-pinned native Blender, Toaster, Playdeck remotion tests. Only synthetic media are used in CI; personal sources stay on the user's local computer.

## Project laws

GRAB ≠ ERASURE.

CROSS ≠ NEW OWNERSHIP.

MIXED PIXELS ≠ UNTRACEABLE IMAGE.

CANDIDATE ≠ SELECTION.

APPLY TO DRAFT ≠ SEAL.

SEAL ≠ FILM RENDER.

RENDER ≠ KEEP.

KEEP ≠ PUBLICATION.

SHARED SOURCE ≠ SHARED AUTHORITY.

## Future frontier

A patch library that makes a grabbed image rectangle a named, independently transportable source artifact would fit reLATTE / reLATTE receipts and the broader cross-repo composition stack. BAND-IQ 013 deliberately limits transfer to the one owner's prepared image set; **no remote or other-owner asset transport is authorized by this slice**.
