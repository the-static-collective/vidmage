# BAND-IQ 007 — A/C: the author reviews the original and the revision

**Status:** experimental source-pinned human interface, stacked directly on BAND-IQ 006 PR #10. No changes to upstream Blender, Toaster or Playdeck. No release, deployment or merge.

## The creative boundary

BAND-IQ 004 reviewed the original VidMage film A and native Playdeck alternative B. The human explicitly asked another question. BAND-IQ 005 preserved the author's question verbatim, proposed three mechanically bounded edits, and performed exactly **one** separately authorized VidMage revision C. BAND-IQ 006 rescanned the real original A and revision C, independently measured actual picture changes, and wrote a local observed-technical-evidence receipt. Until BAND-IQ 007, those two films did **not** have their own dedicated human comparison decision.

BAND-IQ 007 now supplies a **separate local A/C review room**: two independently verified real original/revised VidMage MP4s play side by side, with synchronized playback, independently selected soundtrack and factual before/after window inspector. Above the players, the creator's original question appears verbatim; no model claims to understand its intent.

The author explicitly chooses exactly one:

- **CONTINUE A** — original VidMage film selected for further local creative work.
- **CONTINUE C** — the newly revised VidMage film selected for further local creative work.
- **DECLINE BOTH** — neither performance selected, while both histories remain intact.
- **ASK ANOTHER QUESTION** — record a new, author-written question only. Another render requires separate future source inspection and permission.

Every choice needs a new operator attestation and explicit local-only acknowledgement, and produces one new content-addressed, pair-addressed and **create-only review receipt**. Reopening the same source pair reads that earlier choice unchanged; it cannot silently become a different verdict. The earlier 004 human question, 005 revision receipt, 006 observational receipt and both actual films are separate immutable sources.

**CONTINUE IS NOT KEEP IN PLAYDECK, EXPORT, PUBLISH, DELETE, MERGE OR ANOTHER RENDER.** A low or high pixel difference is not a rating, and deliberate stillness is not a problem to optimize away.

## Evidence required to open A/C

BAND-IQ 007 validates source bytes and exact receipt identities before displaying anything:

1. The original full-song VidMage A and its distinct historical Playdeck B are verified through the actual BAND-IQ 004 original review class, including their distinct source-pinned movie receipts.
2. The creator's signed 004 **ANOTHER_EXPERIMENT** receipt is present. A previous 004 KEEP A, KEEP B or SCRAPE is **not** treated as a new question.
3. The new C film's authentic 005 revision receipt can independently reopen its unchanged original audio, source stills, newly authored scene cards, source Blender paper plan and original Toaster observation.
4. The 005 record points back to the exact 004 human question, original VidMage film and historical Playdeck B film, and the selected revision has not already been marked automatically kept or published.
5. The immutable 006 observation points to the exact 005 revision and 004 review, same full original/revised video identities, same plan/audio/cards and factual author operation. Its native Blender full-duration scan reports, independent picture-window measurements and source overlap claims must be self-consistent. It must explicitly have **no artistic judgment or automatic execution authority**.
6. At the moment the human presses **Seal my A/C decision**, A, C, the historical B film and the older human receipt are independently read again for tampering.

The new A/C compare contract contains the hashes of the original 004 human review and source A/B pair, 005 selected revision, 006 observation, unchanged author question, original VidMage A, newly revised VidMage C, historic Playdeck B, owner-selected operation and source audio. It has a separate SHA-256 identity. It is not a replacement for any earlier receipt.

## Run the actual local room

Once BAND-IQ 004–006 produced the private films and JSON artifacts, run the following from the VidMage repo. BAND-IQ 007 itself requires Python 3.12+ and existing source evidence, not a new native render or Remotion install:

    python -m bridge.band_iq_ac_review \
      --cycle /private/cycle.json \
      --selection /private/original-render-selection.json \
      --vidmage-record /private/original-vidmage-film-record.json \
      --vidmage-movie /private/original-vidmage.mp4 \
      --playdeck-receipt /private/native-playdeck.receipt.json \
      --playdeck-movie /private/native-playdeck.mp4 \
      --record-dir /private/old-004-human-review \
      --revision /private/new-film/band-iq-005-revisions/<revision-sha>.json \
      --observation /private/question-observations/<observation-sha>.json \
      --ac-record-dir /private/band-iq-007-human-ac-review \
      --port 8765 --open-browser

The local browser opens **http://127.0.0.1:8765/**. It serves only the A and C media paths with HTTP byte-range seeking, fixed bundled HTML/JS/CSS routes and a read-only context endpoint. Media are never posted to a provider or GitHub. The first-review source comparator may create/reuse an identical original A/B pair evidence receipt under --record-dir, but never changes the films or earlier human choice.

A separate A/C decision requires a same-origin POST with the session capability token, exactly these fields: decision, operatorAttestationId, rationale, nextQuestion and acknowledgedLocalOnly. Arbitrary paths, other API names, paid/cloud authorities, source uploads, video edits and the older 005 execution route are rejected. The A/C choice is stored under --ac-record-dir/human-ac-<comparisonSha256>.json. The original comparison metadata is content-addressed separately.

A fresh A/C URL cannot be used to trick the old 004 Review Room into replacing its original decision. Another author question is **only recorded**: it does not acquire another 005 proposal set, call Blender, make another movie or authorize public distribution.

## Proof

- Python owner-local tests: python -m unittest -v tests/test_band_iq_ac_review.py
- Browser syntax: node --check ui/band_iq_ac_review.js
- Native end-to-end synthetic proof: tests/test_band_iq_playdeck_native.py, when native pinned Playdeck/Toaster/Blender and local FFmpeg are available.
- Workflow: .github/workflows/band-iq-007.yml — fixed native donor source SHAs, separate pure and actual-media stages.

The pure suite includes A/C source/receipt coherence, rejected forged question or video, real HTTP byte-range seeking, inaccessible directories and forbidden 005 execution route, same-origin/session-token refusal, one irreversible creator decision and subsequent readback/restart. The native run produces actual VidMage A and Remotion B, records an explicit 004 human next question, performs one human-chosen 005 C film, obtains real 006 native Blender picture observations and finally records and reopens a **separate real-film 007 CONTINUE C** human choice. No source films or personal artwork are committed.

## Laws

VIEW != CHOICE.
ORIGINAL != REVISION.
OBSERVATION != PREFERENCE.
NUMERIC CHANGE != AESTHETIC IMPROVEMENT.
QUESTION != PERMISSION.
CONTINUE != PUBLISH.
REVISION != ERASED HISTORY.
FIRST REVIEW != SECOND REVIEW.
SECOND REVIEW != THIRD RENDER.

## Next useful crossing

Promote this isolated experimental A/C room into the main VidMage first-user navigation, alongside Bring, Direct, Make and Revise, without bypassing author permission or exposing their local media. A single human-facing workspace can eventually show the entire lineage (source film, alternative performance, selected experiment, measured outcome, author choice), not force the user to reassemble it from receipt paths. That future front door is not claimed as delivered by BAND-IQ 007.
