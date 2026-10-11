# BAND-IQ 002 — one selected lens becomes a real trial movie

**Experimental / stacked on BAND-IQ 001.** Do not merge automatically. No provider submission, public media, customer assets, private credentials or claimed artist KEEP.

## What is actually new

BAND-IQ 001 perceives a real film, gives six Playdeck-derived cinematic proposals, and remembers an observation. BAND-IQ 002 closes its missing performance seam.

OWNER-AUTHORED MEDIA + ACTUAL TOASTER AUDIO
  → existing VidMage source-bound scene cards + native Blender Paper Director shot plan
  → original full-song VidMage movie (real local OpenCV/FFmpeg)
  → independently source-attributed native 008f scan (first observation)
  → BAND-IQ 001 six-up proposal and optionally author-protected stillness
  → explicit human RENDER_TRIAL selecting one exact proposal SHA
  → real SECOND full-song VidMage movie with selected camera grammar
  → second native 008f scan of actual trial MP4
  → bound, measured BAND-IQ comparison + separately authored KEEP/SCRAPE/HOLD if desired
  → create-only exact media, scene, score, selection and ancestry receipts

Blender 008h harvests a real owned source video into traceable original stills and fragments. Blender 008l applies a tactile treatment to one exactly chosen still. BAND-IQ can verify and bind the 008h original video → specific still → 008l materialized PNG chain to the real scene card used by both full-song movies. Other scene assets must still have exact SHA256 byte pins; an authored direct asset can remain direct.

## Real (and not claimed)

- Playdeck 011 supplies six **cinematic grammar types**. VIDMAGE itself implements local CPU camera transforms for these types in the actual scene-card raster renderer. This **does not run the native Playdeck/Remotion renderer**; it is a typed adapter executing Playdeck-derived grammar.
- The original and trial use the **same** source images, scene cards, shot layout and song. This tests one changed camera variable. It avoids attributing a changed source material to better camera direction.
- Existing Blender 008j builds the actual paper shot plan; its normal rendering is separately available in BAND-IQ 001. VidMage performs the two movie outputs here, not Blender 008j.render.
- Native Blender 008f accepts an 008e-shaped source-attribution plan. BAND-IQ explicitly generates its own 008e-*compatible* adapter from the actual VidMage scene card and source-byte hashes. The plan contains the flag nativeBlender008eExecution:false and does **not** claim Blender 008e originally rendered this film. The Doctor still measures actual MP4 frames and genuine source repetition.
- Native Toaster L BRANCH supplies raw-energy and transient observations; untimed lyrics do not gain fake vocal timing.
- No outside vision model was installed. No semantic object tracking, automatic face interpretation, lip sync, motion synthesis, native Remotion proof, publication or shared hosted service is claimed.

## Native source lock

VidMage base branch: experiment/band-iq-001-evidence-to-next-experiment.

- Composite Blender = cf0256a49ac8aa879cf2a044847d248177fcfad9.
- Native Toaster = 3652c2a96b6b287cda316d1c92daadf7c7417eaf.
- Playdeck Studio 011 vocabulary = 012186fd67f4c4ef1c6591fc5e29cb559b5a80d0.
- All direct native donor operations still require creator authorization and exact source checkout.
- See prior BAND_IQ_001.md for the donor-specific historical heads and correct external-code boundaries.

## Selected-film contract

The selected film envelope has schema "vidmage/band-iq-selected-film/v1", and exactly:
- cycleSha256 and proposalSha256 from BAND-IQ 001;
- sourceVideoSha256 of the already scanned original movie;
- operatorAttestationId and decision "RENDER_TRIAL";
- allowLocalExecution=true, allowPaidProviders=false, allowNetworkUpload=false;
- paperPlanSha256 for the actual Blender native Paper Director plan;
- sceneCardsSha256 for the artist-authored scene/asset assignments;
- audioObservationSha256 and audioSha256 from the original actual native Toaster input;
- assetBindings dictionary of asset IDs to exact real SHA-256 of every image.

The asset bytes are re-hashed, every relative path stays inside the admitted root, and a stale selection is refused. The selected proposal must be a member of the authenticated exact six-up, must address a *non-protected* target window, and must be in proposal-only state.

The separate optional native material lineage envelope has schema "vidmage/band-iq-harvest-material-lineage/v1" and exact fields:
- harvest: original native 008h harvest manifest;
- materialization: original native 008l material receipt;
- boundAssetId: scene-card asset pointing to materialized PNG;
- selectedHarvestArtifactSha256: specific original still's observed hash.

BAND-IQ re-verifies both original native donor record identities, media on disk, the original owned-video SHA, the specific still SHA, the actual 008l input and output bytes, and their binding to the selected scene asset. A crop does not imply semantic subject identity.

## Local command surface

Use owner-local Python 3.12+, FFmpeg/FFprobe, NumPy, OpenCV, Pillow; for genuine Toaster observations use Node 22. No external generation or cloud upload. All media stays out of Git.

1. Existing native donor tools or an authorized creator produce: media, signed-off local scene cards, a real paper-director plan and native audio observations.
2. Generate a source-true native Doctor attribution plan (no false 008e performance):

       python -m bridge.band_iq_film_loop doctor-plan \
         --paper-plan /private/native-paper.plan.json \
         --cards /private/scene-cards.json \
         --asset-root /private/stills \
         --output /private/doctor-scene.plan.json

3. Make an unselected base film through the existing VIDMAGE scene_card_film CLI, with exact plan/cards/Toaster observations, then run Blender 008f on the actual MP4 with doctor-scene.plan.json.
4. Construct BAND-IQ 001 cycle from the real original 008f report; preserve any operator-attested stillness.
5. Review six cinematic questions, author a separate source-locked selection JSON with the exact chosen proposal SHA. This is a *local trial render* authorization, not KEEP or publication.
6. Execute one bounded second movie and its separate receipt:

       python -m bridge.band_iq_film_loop render \
         --cycle /private/cycle.json \
         --before /private/native-before-doctor.json \
         --selection /private/film-selection.json \
         --plan /private/native-paper.plan.json \
         --cards /private/scene-cards.json \
         --observation /private/native-toaster-observation.json \
         --audio /private/song.wav \
         --asset-root /private/stills \
         --base-movie /private/original.mp4 \
         --output /private/trial.mp4 \
         --lineage /private/optional-native-parts-and-material.json

    Omit --lineage if all assets are already authored direct images. When present, exact native lineage is verified.

7. Explicitly run native 008f against trial.mp4, using the **same** source-attribution plan, and separately compare:

       python -m bridge.band_iq_film_loop compare \
         --cycle /private/cycle.json \
         --before /private/native-before-doctor.json \
         --after /private/native-after-doctor.json \
         --film-record /private/band-iq-film-evidence/<film-hash>.json \
         --film-receipt /private/trial.receipt.json \
         --performed-movie /private/trial.mp4 \
         --output-dir /private/reviews

    Optional --human-review holds an exact named decision KEEP, SCRAPE or HOLD plus operatorAttestationId. There is still no publication or editing authority transfer.

## Automated proof

The band-iq-002 GitHub workflow:
- checks six different pixel-transform modes, exact source/card attribution, syntactic correctness;
- checks out native Blender and Toaster at the exact SHAs above;
- creates real synthetic audio and video locally (not uploaded);
- analyzes real synthetic song audio through the native Toaster L BRANCH capture;
- harvests video to actual 008h source stills, materializes a clay image via native 008l;
- composes the same exact material + shot layout into a local baseline movie;
- runs actual native Blender 008f on baseline;
- creates BAND-IQ 001 cycle and six candidates;
- renders a film with the explicitly selected first camera, verifies differing MP4 bytes;
- reruns native 008f, records a paired full coverage comparison and preserves the source movie;
- verifies a second different selected camera makes a genuinely distinct movie;
- refuses unknown proposals, paid access, stale source SHA, altered native ancestry, duplicate outputs, and comparisons against the wrong movie.

## Laws

STILLNESS != WEAKNESS.
ANALYSIS OF ACTUAL MP4 != AESTHETIC CERTAINTY.
EDITORIAL CHOICE != AUTO-KEEP.
SIX PROPOSALS != SIX AUTOMATIC RENDERS.
ONE HUMAN-CHOSEN LENS != NATIVE PLAYDECK EXECUTION.
MATERIALIZED ASSET != ORIGINAL SOURCE.
SCENE-ATTRIBUTION ADAPTER != NATIVE 008E FILM MILL RUN.
SCORE CHANGE != PUBLICATION AUTHORITY.

## Next

A simple VIDMAGE film-facing panel, actual human first-use test, and optional direct Playdeck Remotion cross can follow the proof. The human creator should see BRING / DIRECT / MAKE / REVISE / EXPORT, not see Git hashes until they open an optional Inspector.
