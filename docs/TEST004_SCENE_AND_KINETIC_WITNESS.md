# VIDMAGE Test 004 — Scene-direction and optional kinetic camera

2026-10-10. **Local creator-media experiment. Not a release or accepted final film.**

## Exact crossings

- Native Haunted Toaster audio/L BRANCH observation (donor SHA 3652c2a96b6b287cda316d1c92daadf7c7417eaf): real 184.344-second music file, 6 audio-inferred sections and 2 evidenced lanes, energy + transient-pressure. Vocal-salience remains unavailable.
- Native Haunted Blender Paper Director **plan** (donor SHA cf0256a49ac8aa879cf2a044847d248177fcfad9): 28 proposed full-coverage shot boundaries.
- VIDMAGE owner-local raster rendering: independently proposed assignment of 8 authorized images to the shot plan, followed by non-destructive framing/motion. Outputs: two full-song H.264/AAC MP4s, 640×360 at 12fps, 184.32 seconds.
- Optional Mob Burns trial: 9 Toaster-transient-based motion centers (50, 61, 79, 99, 116, 133, 140, 149, 174 seconds); non-text images only, bounded punch/tilt/recoil, separately rendered and easily bypassed. No animated humans were synthesized.

## Verified output identities

| Local review trial | MP4 SHA-256 | Status |
|---|---|---|
| Plain directed film | 720d8ef4a49a30063861fdbb36963f04428199600f3ff7cacc65842f78fd1e2a | Complete |
| Optional kinetic variant | 350d65211a024190ae9a775680807eff7e4c1008a8e9739a67fec9f8930ae354 | Complete |

Both include the full music and use zero external video generations / provider credits. Source images, recording, video bytes, private manifests and private scene assignments **were never committed to public GitHub**.

## Critical distinctions

- The supplied lyrics lacked measured timestamps. Native Toaster Listener correctly reports ordinary plain text as **evenly distributed / timed=false**, not valid vocal-salience evidence. Its new VIDMAGE gate separates this from an actual timecoded LRC input.
- Song energy sections are **not** verified verse/chorus identity. Scene assignment is an editorial proposal, not an authenticated human KEEP.
- These two completed films used **native Blender Paper Director shot planning**, but their raster animation and MP4 encodes were performed by VIDMAGE's **local Python/OpenCV/FFmpeg adapter**, not Blender's native video render().
- A separate full-length native Blender finalizer attempt **timed out**, produced no valid full-duration receipt, and its partial output was discarded. Do not report native finalization as passed. Test 003's earlier complete native Blender render is distinct and remains a real witness.
- Test 002's inherited FFmpeg reverse/loop issue remains open upstream: https://github.com/the-static-collective/the-haunted-blender/issues/69 .

## Reusable code on this branch

- bridge/toaster_listener_gate.cjs: actual native Toaster lyric parser with explicit timed/untimed classification.
- bridge/scene_card_film.py: generic media-local create-only trial renderer, paper-shot boundaries, owner-authored scene cards, real L BRANCH observation, optional motion, output hashes and receipts.
- tests/toaster_listener_gate.test.cjs: synthetic plain/LRC tests.
- tests/test_scene_card_film.py: synthetic real-MP4 and separate kinetic render, refusal tests, zero-provider path.
- CI uses exact donor SHAs. The public generic renderer is a later integration artifact; identical frames with the owner-local prototype are not asserted.

## Next

Ask the creator to author **a few actual lyric/time anchors** in Toaster Listener, confirm which assets correspond to each, then let Blender's 008j cue-aware director propose an edit. Fix native finalizer performance independently. Only then decide if stronger kinetic movement improves the accepted story.

AUDIO OBSERVATION != VOCAL TIMING. PROPOSAL != KEEP. KINETIC PASS != SOURCE MOTION. RENDER != PUBLICATION.
