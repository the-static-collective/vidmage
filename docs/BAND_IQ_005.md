# BAND-IQ 005 — the next question becomes a human-chosen experiment

Status: **executable experimental, stacked on BAND-IQ 004**. Never auto-merge, release or publish. No provider account, model API or remote media storage.

## What changed

At the end of BAND-IQ 004's two-film review room, the creator can choose ANOTHER EXPERIMENT and write a question. 005 preserves that question **verbatim** as evidence, not a machine instruction.

The source-pinned next-question compositor makes **three bounded mechanical possibilities**:
1. **SWAP_CARD:** change ONE shot to another *already source-authorized* image with **different source bytes**. The other source images, shot timings, original videos, audio and human review do not change.
2. **REFOCUS_CARD:** choose a new normalized focal point for ONE shot. A new scene-card alias carries the *same original image path/SHA* but an independently revised focus; other occurrences using the original image are unchanged.
3. **CHANGE_LENS:** apply another one of the six already pinned Playdeck-derived camera grammars inside the **same previously selected window**. Do not add new vision or interpret the artist's question as a render command.

The creator must take **a second, independent action**: select one experiment, supply the exact shot/image/focus/lens values, attest the choice, and confirm one owner-local trial. Without that act there is **NO render**.

All three possibilities are generic. There is no claim that NLP extracted causal intention from the author's words or that the numerical Doctor scores understand aesthetics.

Once a trial is chosen, 005 performs an actual **new local VidMage MP4 render** using the same exact native Blender Paper Director shot timing and native Toaster observed audio, and writes an immutable SHA-addressed revision record. It preserves the original two films and 004 review. The new revision record contains the author's own next question, precise selected variable, **full edited scene cards, source Paper Director plan, original Toaster observations**, paths to verified local media and hashes, and a newly checked video receipt.

The resulting local project can be **reopened and validated**, including re-reading the film, original audio, source images, exact scene cards and source-native plan, *without overwriting old works*. A rendered revision remains **unselected** until a new human review. If rendering produces byte-identical media, the record explicitly says that no changed media was established.

## The user-facing route

VIDMAGE's existing BAND-IQ 004 review room accepts five optional **explicit local source paths** to activate 005 (all or none):

    python -m bridge.band_iq_review \
      --cycle /private/film-cycle.json \
      --selection /private/initial-render-selection.json \
      --vidmage-record /private/vidmage-film-record.json \
      --vidmage-movie /private/vidmage-film.mp4 \
      --playdeck-receipt /private/playdeck-film.receipt.json \
      --playdeck-movie /private/playdeck-film.mp4 \
      --record-dir /private/band-iq-reviews \
      --next-plan /private/native-blender-paper.plan.json \
      --next-cards /private/author-scene-cards.json \
      --next-observation /private/toaster-lbranch-observation.json \
      --next-audio /private/song.wav \
      --next-asset-root /private/source-stills \
      --port 8764 \
      --open-browser

Inside the same **http://127.0.0.1:8764/** review page:
- Watch original A and B and choose ANOTHER EXPERIMENT with a written actual question.
- The page reveals the original question verbatim and the three permitted experiment categories.
- Choose a shot and known authorized alternative image, or one shot's 2D focus, or another pinned lens.
- Sign a **new** local trial attestation and explicitly confirm rendering one trial. No global automatic KEEP; no spend/upload permission; no arbitrary file path accepted from the browser.
- The browser displays the third **actual newly rendered MP4** after the explicit action, alongside its output SHA. It remains a new *unselected* film.

The Python service binds only 127.0.0.1. Next-question GET produces proposals only. POST uses the same one-session bearer capability and strict same-origin check as the 004 review, rejects undeclared fields, and derives the output path from the verified review and second selection. Files are owner-local; the service never accepts a browser-supplied input or output filesystem path or shell command.

The service requires source plan/cards/audio to match exact hashes from 004's original selected film. An unrelated video, stale scene plan, changed image, unapproved provider permission or non-004 human question stops at HOLD.

### Source-only CLI option

Independent of the browser, a fully typed owner-local CLI exists for scripted or accessible use:

    python -m bridge.band_iq_next_question propose \
      --cycle /private/film-cycle.json \
      --selection /private/initial-render-selection.json \
      --vidmage-record /private/vidmage-film-record.json \
      --vidmage-movie /private/vidmage-film.mp4 \
      --playdeck-receipt /private/playdeck-film.receipt.json \
      --playdeck-movie /private/playdeck-film.mp4 \
      --record-dir /private/band-iq-reviews \
      --plan /private/native-blender-paper.plan.json \
      --cards /private/author-scene-cards.json \
      --observation /private/toaster-lbranch-observation.json \
      --audio /private/song.wav \
      --asset-root /private/source-stills \
      --output /private/band-iq-next-questions

The output is a **create-only SHA-addressed JSON** containing the three proposals, their exact allowed shot IDs and authorized alternatives.

The creator writes an explicit local trial authorization with schema vidmage/band-iq-005-trial-authorization/v1 and EXACT fields:
- questionSetSha256, proposalSha256, operatorAttestationId;
- decision = RENDER_ONE_LOCAL_TRIAL;
- shotId, replacementAssetId, newFocus, newLensId (only those relevant to chosen proposal; all other fields must be JSON null);
- allowLocalExecution = true, allowPaidProviders = false, allowNetworkUpload = false.

To run it, call **render** with the same arguments as propose, plus:
- --question-set /private/band-iq-next-questions/<hash>.json
- --authorization /private/second-independent-artist-selection.json
- --output /private/new-vidmage-trial.mp4

The CLI writes the movie, its genuine ffprobe/FFmpeg receipt, and a SHA-addressed revised editable project JSON in the output directory's band-iq-005-revisions folder.

Reopen an already performed trial:

    python -m bridge.band_iq_next_question reopen \
      /private/band-iq-005-revisions/<revision-hash>.json

The reopen command independently verifies media, audio, source images, edited source bindings, the native Paper Director plan and original Toaster observation. It returns an editable scene-card snapshot and an independent source receipt; it does **not** re-render automatically.

## Native proof

.github/workflows/band-iq-005.yml:
- Pure test: all bounded choices, refusal of mismatched shot/source, changed question SHA, fake provider permissions, arbitrary fields, no auto-run, and inherited human review integrity.
- Native test: exact pinned Toaster + Blender + Playdeck commits, actual source audio, native paper plan, two distinct real baseline trial MP4s, an explicit signed ANOTHER EXPERIMENT with written next question, three source-bound proposals, **separate creator choice**, a real third MP4 and newly edited project, strict source-integrity proof, and successful reopening.
- Browser integration: localhost serves proposals after actual 004 review, rejects cross-site third-party execution, makes an independently authorized local trial, streams its real MP4 with byte ranges, refuses repeat execution, and verifies old films remain.
- UI script syntax, no external scripts, no private creator media in GitHub.

## Actual authority laws

HUMAN QUESTION != MACHINE COMMAND.
QUESTION != INTERPRETATION.
PROPOSAL != SECOND SELECTION.
SECOND SELECTION != KEEP.
ONE RENDER != AUTOMATIC FUTURE RENDERS.
SAME SOURCE IMAGE != SAME SHOT FOCUS.
REFOCUS ONE SHOT != REFOCUS ALL SHOTS.
SCRAPE != ERASURE.
OLD REVIEW != NEW REVIEW.
LOCAL RECEIPT != PUBLICATION.
OBSERVATION != ARTISTIC MEANING.

## Next seam

After the creator chooses the new trial, a fresh actual Blender 008f scan of it could be compared to the previously selected local film. That is a distinct next experimental observation, not an excuse to let a lower score choose the art. A subsequent human Review Room would compare original versus revised video with separate source-proof and KEEP permission.

No public VidMage deployment or full Start / Bring / Direct / Make / Revise / Export product launch is claimed by this experimental branch.
