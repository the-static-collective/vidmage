# BAND-IQ 003 — one creative question, two independent native performances

Status: experimental VidMage branch stacked on BAND-IQ 002. No automatic merge or release.

## The integration

BAND-IQ 002 already proves a selected Playdeck-derived cinematic grammar creates an actual second VidMage MP4. The previous Playdeck crossing borrowed only its six-lens vocabulary, not the native renderer.

BAND-IQ 003 adds a new independently executed path: native Playdeck Remotion, using the pinned actual Playdeck code and its own card layout, atmosphere, memory, camera and topology behavior.

The shared exact sources are: the original already-observed full-song baseline MP4 identity, native Toaster audio observation, actual source audio bytes, native Blender Paper Director shot plan, artist-authored scene cards and exact source image SHA-256s, and one human-attested BAND-IQ proposal selected for a bounded trial.

The outcomes are *two different films*, each verified from its real MP4 bytes, with distinct source-pinned receipts and a single content-addressed dual-renderer comparison record.

## Three pinned repos

- Playdeck Studio 011 source at 012186fd67f4c4ef1c6591fc5e29cb559b5a80d0.
- Haunted Blender composite at cf0256a49ac8aa879cf2a044847d248177fcfad9.
- Haunted Toaster L BRANCH at 3652c2a96b6b287cda316d1c92daadf7c7417eaf.

No upstream Git history is altered. The Remotion render runs the exact native Playdeck Composition registered in packages/render-remotion/src/Root.tsx. Its PlaydeckComposition.tsx, frankenCinematic.ts, CardLayer.tsx, layout.ts and atmosphere/memory components are native Playdeck code, not a VidMage replica.

### 003 fixes a vital performance boundary

BAND-IQ 002's prior selected camera was not bounded to the operator-chosen window despite the proposal's exact target. 003 requires targetStart and targetEnd and changes the VidMage camera *only* within that interval, still protecting text assets.

Native Playdeck's camera is also time-bounded: a single CompositionPlan custom event has the precise selected interval and params.franken.cinematic with the five native Studio 011 camera/topology/rhythm/relations/memory grammar values. The plan deliberately does not supply global studioFranken cinematic metadata. Native Playdeck's normal ambient card behavior may still occur outside that interval; the *selected direction* may not.

STILLNESS != WEAKNESS.
TARGET WINDOW != FULL SONG.
HUMAN RENDER_TRIAL != HUMAN KEEP.

## Author-selected native Playdeck transport

The adapter bridge/band_iq_playdeck_native.py independently rechecks:

- full six-up cycle SHA and the selected proposal;
- original Doctor report/baseline movie identity;
- typed selection with creator attestation and local-only permission;
- native paper plan, ordered scene-card source assignments, exact source image SHAs;
- native Toaster L BRANCH and exact audio file SHA;
- native Playdeck Git HEAD SHA and expected source modules.

It then creates one card per actual shot occurrence, preserving reuse of the same logical source under the same asset ID, writes TrackSpec from the real song, and creates a genuine Playdeck CompositionPlan with selected cinema active only during the selected time interval.

All authorized image/audio bytes are rehashed, temporarily copied into a unique owner-local folder under the native Remotion public root (needed by Playdeck staticFile), and rehashed after copying. That temporary folder is deleted whether the actual render succeeds or fails. The already installed native Playdeck Remotion executable is used to produce a real MP4, which must contain both soundtrack and picture with full source duration. The actual MP4 SHA and its native Playdeck plan/props identity are sealed in an independent create-only receipt; no file is uploaded to GitHub.

The source must be locally pinned and npm dependencies already installed at that exact checkout. Remotion and Chrome may require significant local compute and installation. No paid provider or external creative generation.

## Commands

Use Python 3.12+, FFmpeg, Node 22, local pinned Blender/Toaster/Playdeck checkouts, and their normal native dependencies.

Render an independent Playdeck trial:

    python -m bridge.band_iq_playdeck_native render-native \
      --cycle /private/cycle.json \
      --before /private/native-doctor-before.json \
      --selection /private/selected-lens.json \
      --plan /private/native-paper-plan.json \
      --cards /private/editor-scene-cards.json \
      --observation /private/toaster-native.json \
      --audio /private/song.wav \
      --asset-root /private/source-stills \
      --baseline-movie /private/baseline.mp4 \
      --playdeck-root /private/pinned-playdeck \
      --output /private/native-playdeck-trial.mp4

The new film receipt is written alongside the output as native-playdeck-trial.receipt.json.

After BAND-IQ 002 produces its own actual trial with the *same* exact selected proposal:

    python -m bridge.band_iq_playdeck_native compare-pair \
      --cycle /private/cycle.json \
      --selection /private/selected-lens.json \
      --vidmage-record /private/band-iq-film-evidence/film-hash.json \
      --vidmage-movie /private/vidmage-trial.mp4 \
      --playdeck-receipt /private/native-playdeck-trial.receipt.json \
      --playdeck-movie /private/native-playdeck-trial.mp4 \
      --output-dir /private/dual-renderer-comparisons

This independently verifies the two real output hashes, both source branches, the same artistic question and operator selection, the input images/audio identity, and marks aesthetic equivalence as unknown, not asserted.

## Automated proof

The new band-iq-003 workflow:
1. Runs pure source/grammar tests with no donor runtime installed.
2. Clones exact Blender, Toaster, Playdeck commit SHAs in a disposable environment.
3. Installs native Playdeck workspace dependencies and CPU-only media tools.
4. Analyzes real synthetic audio with native Toaster and constructs a real native Blender Paper Director shot plan.
5. Renders a source-true baseline using VidMage, obtains native Blender 008f observation, builds the six proposed lenses.
6. With one explicit human-selected synthetic test decision, renders a VidMage selected-window MP4.
7. Uses actual native Playdeck Remotion to produce a separate MP4 from the same source materials and selected window.
8. Verifies original source identity and two different actual MP4s, full duration, audio/video streams, immutable compare-pair, no auto-KEEP, no publication, and refusal of tampering and duplicate output.

**Truth boundary:** Playdeck's animated card arrangements are different from VidMage's shot-card raster order. The films need not look the same and are not pixel-equivalent. This is a shared-input/shared-intent comparison, not a reference-fidelity test or verified aesthetic improvement.

Next useful human surface: show the two actual trial outputs side-by-side, let the creator KEEP one or neither, and only then consider new evidence-derived experimental branches.
