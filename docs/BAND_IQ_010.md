# BAND-IQ 010 — The Storytable

**Experimental, working local creator-authored cinema source.** This branch stacks on unmerged BAND-IQ 009 PR #13. No automatic merge, public Abundent deployment, cloud provider, paid generation or auto-KEEP.

## Why this exists

BAND-IQ 009 gave someone a genuinely working Front Porch: upload a song, bring pictures, sign source rights, prepare native Toaster/Blender paper, separately authorize a pair of local VidMage and native Playdeck films, and review those films in the existing 004–008 workbench.

It still assigned pictures provisionally in upload order. **That initial placement was the machine's suggestion, not a story the artist had actually authored.**

BAND-IQ 010 inserts a real **Storytable** between paper preparation and film authorization.

### What the human can now do

The song plays **from the real, owner-local prepared WAV**, with browser controls. Native Blender Paper Director's actual contiguous time windows appear as tactile shot cards, labeled in seconds. Clicking a shot moves the song cursor to its start. During playback the selected shot follows the playhead.

For **each actual timed shot occurrence**, the creator can:
- Pick any particular already-owned image (not an external image URL).
- Set horizontal and vertical focal attention on two 0–100% dials.
- Explicitly protect writing or existing graphics from the renderer's ordinary subject-focused treatment.
- Step through the timeline or jump directly from one shot to another.
- Reuse one photograph in multiple positions with different focal points and text-protection settings.

The preview is a **framing guide**, not an assertion of pixel-perfect resemblance to the final MP4. The original native Paper Director timing stays intact. The original song and uploaded photos remain intact, as do the 009 machine-provisional scene-card files.

When the artist has made their choices, they **seal the Storytable with a new human attestation**. The signature records the exact image, original source SHA, time interval, focal point and protect-text choice of every shot. This is a **create-only, independently re-openable, SHA-bound receipt**, not a render request.

The camera choice and **second explicit film-making authorization** remain separate from that seal. Until the Storytable has been sealed, the new Front Porch refuses to render either VidMage or native Playdeck—even if an older tool attempts to call the original 009 render API directly.

### Why the two renderers really see the artist's work

A signed 010 receipt produces a new set of *authored* VidMage editorial scene cards:

- Existing native shot IDs and start/end boundaries are preserved exactly.
- Every shot occurrence gets its own asset alias, even if two shots point to the same underlying source bytes. That allows independent crop/focus and protect-text behavior without modifying the original.
- Every alias retains the exact owned prepared PNG path and original SHA from BAND-IQ 009's paper tray.
- The native local VidMage OpenCV/FFmpeg baseline, source-aware Blender 008f scan, explicitly authorized lens trial, **VidMage A**, and **native Playdeck Remotion B** all consume the **same author-sealed cards**.
- Actual filmed-card hashes are preserved in the 009 selected-render evidence and in the 008 Workbench's private project pointer map.
- The first film performance receipt now records both \`sourceStorySha256\` and \`authoredCardsSha256\`. A subsequent project restart checks both against the actual existing local files.

The original 009 paper cards are **never silently replaced**. The new file is \`storytable/authored-scene-cards.json\`. The film isn't an inferred response to the user's creative question: it is a consequence of their explicit source and framing choices.

### Sequence on the Front Porch

1. **Bring:** one real song and 2–12 owned images, as in 009.
2. **Consent:** rights and local derivatives independently authorized, as in 009.
3. **Prepare:** exact-pinned native audio observations and Paper Director's actual song-timed window plan, no film.
4. **Storytable:** hear the local song; choose every frame's source, focal point and text protection; seal with a human attestation.
5. **Choose camera:** one of the six earlier native Playdeck cinematic languages; an entirely new named authorization permits the actual A/B pair.
6. **Watch and choose:** the 008 Workbench and 004 A/B Review Room are exactly the earlier real implementations. Their 005–007 question laboratory and alternate-film choice remain separately gated.

Any file or receipt tampering becomes HOLD, never fallback to the old machine-provisional image order. Neither the 010 Storytable seal nor the camera choice authorizes publication, source erasure, paid credits, uploading outside the owner's machine, human KEEP or a recursive new experiment.

## Local command

Same local command as 009, with this new branch checked out:

    python -m bridge.band_iq_front_porch \
      --workspace /private/vidmage-projects/my-song \
      --blender-root /private/donors/haunted-blender \
      --toaster-root /private/donors/haunted-toaster \
      --playdeck-root /private/donors/playdeck \
      --port 8767 --open-browser

Open **http://127.0.0.1:8767/**. All actual media work is owner-local, browser files are sent to the same loopback server only, and the original pinned native engines must still be installed. This branch is **not a hosted zero-install product**.

A project that already rendered two films under 009 can still be viewed via the old 009/008 scripts; BAND-IQ 010 applies to new first-film projects and requires new sealed shot choice *before* rendering.

### On-disk artifacts

Existing files:
- \`original/song.*\`, \`original/images/image-XXX.*\` — original uploaded bytes.
- \`consent.json\` — actual source-rights attestation.
- \`paper-tray/song.wav\`, \`source-XXX.png\`, \`paper-plan.json\`, \`scene-cards.json\`, \`toaster-observation.json\`, \`proposal.json\` — native preparation and provisional source planning.

New files:
- \`storytable/story-seal.json\` — owner-signed, create-only timed shot and source receipt, containing \`storySha256\`.
- \`storytable/authored-scene-cards.json\` — shot-occurrence-specific, independently source-verifiable scene-card inputs with their own focal positions and protect-text treatment.
- \`first-performance.json\` — extended native A/B film result containing \`sourceStorySha256\`, \`authoredCardsSha256\`, the original audio/image and film hashes.
- \`private-workbench.json\` — pointer map now directs downstream workbench revisions to the *human* authored cards instead of the original provisional cards.

The source IDs contain no arbitrary URLs. Filenames from an HTTP request cannot become filesystem paths. In the browser, the only added mutation route is a same-origin, session-token protected exact JSON POST to \`/api/porch/story/seal\`, capped at 75 KB and rejecting any unknown source image IDs, shot IDs, extra keys, NaN/out-of-bound focus or unapproved release authority. Read-only song playback is a bounded, source-verified WAV endpoint with byte-range support; image previews reuse the fixed 009 owned-image routes.

## Proof

- \`tests/test_band_iq_storytable.py\`: two real decoded source pictures; verifies two shot occurrences sharing one underlying image with **different** focus/text protection, exact source/shot-time evidence, first human seal and immutable re-open, changed scene-card refusal, changed source-byte refusal, wrong shot/source/focal format rejection and attempted provider/network/publication escalation refusal.
- The older \`tests/test_band_iq_front_porch.py\` **native test is updated**: the full 009 genuine local song/images → Toaster/Blender preparation → VidMage+Playdeck A/B film → separately signed human first review → restart path now explicitly **fails without** a 010 human Storytable, then seals an actual reassignment and focal-point edit, makes the real third-party-native movie pair with that source map, verifies 010 SHA links into the new Workbench, and reopens them. No personal media leaves GitHub's ephemeral synthetic CI runner.
- \`.github/workflows/band-iq-010.yml\` runs a separate small source/refusal/JS validation job, followed by exact SHA-pinned native Blender \`cf0256a...\`, Toaster \`3652c2a...\`, Playdeck \`012186f...\` and actual local media execution.

### Deliberate boundaries

- NATIVE PAPER TIMING != HUMAN CHOICE OF PHOTO.
- HUMAN STORY SEAL != PERMISSION TO RENDER.
- SOURCE SAME IMAGE != SOURCE SAME OCCURRENCE.
- FOCUS GUIDE != FINAL RASTER PROOF.
- TEXT PROTECTED != CONTENT MODIFIED.
- TECHNICAL MEASUREMENT != AESTHETIC PREFERENCE.
- FIRST TWO FILMS != FINAL CUT.
- KEEP != PUBLISH.
- HISTORY != DISPOSABLE DATA.

## Next useful slice

A local pre-render **preview filmstrip** that extracts only a few still frames from the actually authored VidMage arrangement, and optionally a nondestructive cut-marker proposal based on song structure. It should respect 010's sealed source assignments and distinguish temporary sketch previews from a rendered first-film performance. That future capability is not claimed here.
