# BAND-IQ 011 — The Living Filmstrip

**Source-real pre-render sample frames; not a movie or cinematic judgment.** This experimental branch stacks directly on BAND-IQ 010 PR #14 and changes only VidMage, not the pinned native Blender, Toaster or Playdeck repos. No merge, paid provider execution, network upload, publication or auto-KEEP.

## The small wonderful thing

The creator finishes an ordinary action in the Front Porch: they bring an owned song and photos, let native Toaster and Blender create a paper plan, and manually choose **which owned picture goes in every song-timed shot, where the focal point belongs, and whether writing should be protected**. They seal that complete 010 Storytable with their own identity. Previously, the next step was a full native A/B render.

BAND-IQ 011 places **Develop my living filmstrip** between the 010 seal and the full movie. It samples actual raster frames from those exact human-created source choices, using the **same VidMage \`scene_card_film.frame_for\` renderer** that makes the unkinetic baseline. The output is three static frames from each selected real song window, at 12%, 50% and 88% of the available 12-fps native frames within that window, without making a video. The user can click a sampled frame and seek the **actual original prepared WAV** to that sampled time.

The filmstrip is deliberately tactile: groups of three exposed little frames labeled with their source shot and time, inside the analogue Front Porch. Underneath the attractive surface is a documented, verifiable image-source and frame-timing record.

It is **not** an approximate invented AI shot, a model's semantic guess, a moving performance, an exact final movie screenshot after FFmpeg encoding, or a Playdeck render. It applies no cinematic lens, kinetic pulse, soundtrack remix, provider upload, artist KEEP or full-song motion evaluation. The real two distinct A/B movies still require an entirely separate explicit choice of camera grammar and render authorization.

### Important limit for long songs

For 1–36 native shot windows, all are sampled. When Paper Director creates more than 36 windows, this source preview samples exactly 36 **evenly distributed** windows, preserving the first and last. Each sampled window has exactly three stills. The UI explicitly says how many were sampled out of the total, and **omitted windows are not judged poor or rejected**. The full native movie still receives the entire originally sealed Storytable.

Max source-bound work is 108 static 640x360 JPEG frames, with immutable references rather than a generated MP4. The preview shows real authored focus and protect-text presentation under the VidMage raster function; it cannot promise the same camera movement, codec texture, full audio sync, native Playdeck composition or exact later lens selection.

## Three separate permission crossings

1. **Rights and local copies (009):** named creator supplies authentic sources and explicitly authorizes local derivatives. This action does not render.
2. **Authored shot choices (010):** creator signs the complete paper-timed image/framing table. This action does not render or publish.
3. **Source-real sample preview (011):** creator explicitly clicks \`Develop my living filmstrip\` and accepts that local images are **sketch samples**, not a film. New same-origin, session-token protected exact POST \`/api/porch/filmstrip/make\`, with immutable Storytable SHA, \`makeLocalSketch:true\`, \`acknowledgeSketchNotFilm:true\`, and public/provider/network flags false.
4. **Actual movie authorization (009, retained):** a **different** named human consent to render exactly two unselected native A/B movies, after picking a particular camera lens. The 011 preview does **not** satisfy, imitate or grant this authority.

Creating or revisiting a preview never updates the original image files, the 010 seal, the native Paper Director timing, the real audio, or the initial A/B selection. The signed manifest is create-only, and repeated preview requests return the identical previously verified frames instead of recomputing them.

## Actual source mechanics

Implementation: \`bridge/band_iq_living_filmstrip.py\`.

- Requires the complete 010 \`storySha256\`, \`authoredCardsSha256\`, native plan identity and exact original source hashes.
- Validates the same local \`scene_card_film.validate\` input contract as VidMage's native raster renderer. Every sampled original frame index is an integer at **12 fps**, owned by its actual native shot interval; no invented durations.
- Calls the same \`frame_for\` function with measured Toaster \`raw-energy-envelope\`, per-shot focus, per-shot protect-text mode and actual elapsed shot progress. Kinetic pulses and cinematic lens passes are explicitly disabled, matching the source-plain VidMage baseline.
- JPEG samples are generated into a same-parent **temporary directory**, then moved into the final private directory only after every frame, its SHA and the complete \`filmstrip.json\` manifest exists. A failed preview cannot become a half-complete final album.
- \`filmstrip.json\` includes the exact sealed Storytable/plan/cards/Toaster/audio hashes; each actual source window, original authored image SHA and timed sample frame index; image SHA for every generated JPEG; evidence that this is a sketch with no generated movie, provider permissions or automatic publishing. The entire manifest has its own \`filmstripSha256\`.
- Readback checks the manifest SHA, source image bytes, all sample frame indices/timings and every actual JPEG's SHA. An altered file or rehashed fake timing is a HOLD. Browser GET only serves fixed number-pair routes \`/api/porch/filmstrip/frame/{sampledWindowIndex}/{0|1|2}\`; no user-provided path.
- If a preview exists when the owner separately authorizes their A/B films, the existing first-performance receipt also records \`sourceFilmstripSha256\`; restart verifies it again. The movies **still use the full author-sealed Storytable**, never a truncated source filmstrip.

All media remains on the same computer: originals in \`original/\`, normalized working images and WAV in \`paper-tray/\`, authored scene cards in \`storytable/\`, **sketch frames in \`living-filmstrip/\`**, and eventually real MP4s in \`first-films/\`. None are committed to GitHub or uploaded to paid providers.

## Real local usage

Use the same owner-local Front Porch as BAND-IQ 010, with this branch checked out and its pinned native requirements installed:

    python -m bridge.band_iq_front_porch \
      --workspace /private/vidmage-projects/your-song \
      --blender-root /private/donors/haunted-blender \
      --toaster-root /private/donors/haunted-toaster \
      --playdeck-root /private/donors/playdeck \
      --port 8767 --open-browser

Open **http://127.0.0.1:8767/** on that same machine. After arranging and signing the actual Storytable, develop the bounded frame samples, inspect them against the music, then independently authorize the complete A/B performance only when you decide. There is no need to type JSON.

This is real local source-driven software, not yet a public zero-install website. It needs installed FFmpeg/FFprobe, Python 3.12, OpenCV, Pillow, Node and pinned Blender/Toaster/Playdeck to perform the complete 009–011 chain.

## Evidence

- \`tests/test_band_iq_living_filmstrip.py\`: true decoded color source images; two human-ordered shots reuse **one image** with different focus and protect-text. Actual raster image samples on native time indices, no MP4, exact JPEG hashes, immutable readback, forged/rehashed time index and source modification refusal, privilege escalation refusal, bounded 36-window sampling integrity.
- Extended \`tests/test_band_iq_front_porch.PorchNativeTests\`: real synthetic-song media upload and explicit source permissions → native Toaster/Blender paper → genuinely authored 010 Storytable sealed **through the HTTP API** → separate preview request **through the HTTP API** (cross-site attack refused) → real JPEG fetch, unknown-image route refusal and identical on-repeat source preview → full genuine VidMage A and pinned Playdeck Remotion B MP4s → explicitly signed human A/B decision and successful private restart, with the original filmstrip SHA still bound to the films.
- \`.github/workflows/band-iq-011.yml\`: separate source/HTTP/JS validation and actual native synthetic-media A/B continuity stages using pinned SHA Blender \`cf0256...\`, Toaster \`3652c2...\`, Playdeck \`012186...\`. No actual personal art files committed.
- Historical 009/010 workflows also rerun on the stacked PR, to ensure the preview doesn't bypass the original consents.

## Laws

SKETCH ≠ PERFORMANCE.

SOURCE-REAL PIXEL ≠ FINISHED MOVIE.

SAMPLED WINDOW ≠ ALL WINDOWS.

FOCUS ≠ MOVEMENT.

FRAMING GUIDE ≠ FILM KEEP.

A HUMAN STORY ≠ AUTOMATED ARTISTIC JUDGMENT.

NO MEDIA PUBLICATION WITHOUT A NEW HUMAN CROSSING.

## Next open frontier

A tiny **nondestructive before/after contact sheet** for *unsealed* candidate story changes, clearly distinguished from the verified, sealed 011 preview, would let the artist try alternate focal dials and shot-image choices without writing or modifying a signed source receipt. The decision to keep a candidate would still need a separate author seal. Not included in this PR.
