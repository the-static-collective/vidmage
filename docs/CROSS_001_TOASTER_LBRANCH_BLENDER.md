# VIDMAGE CROSS-001 — Toaster L BRANCH × Blender Paper Director

**Status:** Tested integration candidate; not a production creative mode or selected final video.

## The crossing

Native **Toaster** (`3652c2a96b6b287cda316d1c92daadf7c7417eaf`) owns `inspectAudio`, `deriveResponseWitness`, and **L BRANCH** `buildLaneBank`. Native **Blender** (`cf0256a49ac8aa879cf2a044847d248177fcfad9`) owns `scene_growth.normalize_timing`, `paper_director.plan`, and `paper_director.render`. VIDMAGE owns only the versioned, bounded, *proposal-only* bridge in `bridge/`.

```text
authorized local audio
  ↓ [native Toaster inspectAudio + response witness]
L BRANCH lane bank: raw energy, transient pressure; vocal absent if untimed
  ↓ [VIDMAGE bounded projection, source hashes and separate adapter schema]
normalized gates + proposal only
  ↓ [native Blender Paper Director plan + render]
alternate camera-framed version of previously made complete movie
  ↓
separate output hash + render receipt; no source rewrite or implied selection
```

## What L BRANCH specifically contributes

Native lane IDs `raw-energy-envelope`, `transient-pressure`, and optional `vocal-salience` retain their provenance and evidence classes. Native strategy **templates** such as `breath-led` and `pressure-counterpoint` suggest how music may influence a picture. **This v0 adapter does not synthesize an accepted Toaster L BRANCH Mix Plan, fabricate a ResolvedTimeline binding, or render Toaster's candidate ecology**. Its VIDMAGE camera plan is a clearly marked downstream proposal.

When lyrics are supplied as plain text but lack verified timestamp alignment, **vocal-salience stays absent**. Section boundaries are algorithmically audio-inferred; labels such as `Lift` are not assertions about choruses or lyrical meaning.

## Owner-local witnessed run (Blue Rosemary, private inputs not committed)

- Audio: 184.344 seconds. Native Toaster found **6** sections and **2** available lanes. Native lane-bank hash `2f3c95a0485420cee23531e34c610b0f24cca8dd7ae4b24bd2d67a319cfff3bd`.
- Used `breath-led` as a test *proposal*, not a human-approved aesthetic decision.
- Blender Paper Director proposed/rendered **28** shots against a completed 008e source movie; first and last views remain explicit `ESTABLISH` and `RETURN`.
- Actual local output: **184.416667s**, H.264 + inherited music audio, full coverage, SHA-256 `6bbdc937b846535614934d5fec360c932a9e85426935214998156d31306b6147`.
- The existing source film's flawed ordering and mirrored/awkward text is **not corrected** by reframing. This layer governs view selection, not which image should illustrate a lyric. More visual change than 008f's tiny heuristic improvement, but no measured aesthetic superiority is claimed.
- Media, complete private manifests, song, still images and render are stored owner-locally only; GitHub holds *result metadata and synthetic regression*, not a public user-media upload.

## Source setup (local)

Requires `node >= 22`, Python 3.12, `ffmpeg`, `ffprobe`, `Pillow`, plus both repos checked out at exact SHAs in `donors.lock.json`.

```sh
node bridge/toaster_lbranch_capture.cjs \
  --toaster-root /path/to/pinned-toaster \
  --audio /path/to/authorized.mp3 \
  --out /private/toaster-observation.json

PYTHONPATH=/path/to/pinned-blender:. python3 bridge/blender_director_cross.py \
  /private/toaster-observation.json /private/blender-proposal.json \
  --strategy breath-led
```

The adapter writes an **unselected proposal**, not an authorized creative choice. After independent human inspection and permission, a test harness can pass `proposal.paperDirectorPlan` to the native `haunted_blender.paper_director.render` function with a separately authorized local base movie. This experimental receipt is distinct from a published video.

## Verification

`tests/test_lbranch_blender_cross.py` uses synthetic audio and actual native code to verify:
- exact upstream donor operation and bank identity;
- missing vocal lane is not forged;
- deterministic repeatable plan and full coverage;
- bad section bounds, fake render authority, or unsupported vocal strategy refuse;
- actual FFmpeg H.264 output plus SHA-matching Blender receipt;
- existing output cannot be overwritten.

GitHub workflow `lbranch-blender-ci.yml` fetches **exact commits**, not mutable donor HEADs, then runs tests. Upstream commits and CI evidence remain separately linked through the lockfile.

## What's next

An **intentional director/casting pass** should decide scene-to-lyric relationships and ending-cover placement using human-approved footage/asset roles. Once grounded source selection is solved, the parked optional **multi-pass kinetic 'Mob Burns'** camera layer can be evaluated independently.

**L BRANCH EVIDENCE != EDITORIAL SELECTION != FINAL PUBLICATION**.
