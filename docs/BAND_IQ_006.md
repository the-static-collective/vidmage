# BAND-IQ 006 — The Question Laboratory

Status: executable experimental VidMage code, stacked on BAND-IQ 005 PR #9. No merge, release or deployment. Synthetic CI only; original creator media stays local.

## What the lab actually does

A person watches two real films, explicitly chooses ANOTHER EXPERIMENT and writes an actual question. BAND-IQ 005 offers three bounded operations (one image swap, one shot reframe, another already pinned camera lens); the person separately authorizes one and creates a third, still-unselected MP4.

BAND-IQ 006 observes the two relevant actual MP4s: the reviewed VidMage source film A and its locally created revised film C. It does not compare the original Playdeck B as if B were the edited source. It connects those observations to the unchanged human question and the selected operation:

Author's literal question → exact operator change → actual original movie + actual revised movie → two native Blender 008f scans with separately correct original/revised scene-card attribution → independent FFmpeg frame changes → per-window inspectable source and pixel observations → three human-only follow-up questions.

No LLM interprets the prose as authority, and no technical score decides which film the creator wants.

## Actual source locks

- Blender 008f Weakest Window Doctor (real imported native code): commit cf0256a49ac8aa879cf2a044847d248177fcfad9.
- Toaster L BRANCH audio witness: commit 3652c2a96b6b287cda316d1c92daadf7c7417eaf.
- Playdeck Studio 011 original second film: commit 012186fd67f4c4ef1c6591fc5e29cb559b5a80d0.

For the different original and updated still assignments, BAND-IQ creates two different 008e-compatible source-attribution plans. Both explicitly assert nativeBlender008eExecution:false; native Blender 008e Film Mill did NOT create VidMage's MP4s. Only the real Blender 008f Doctor scan is claimed here.

Actual video pixels are sampled at four grayscale frames/second, 64×36 resolution. Window rows include measured mean absolute pixel difference, percentage of sampled frames exceeding 2% pixel difference, real source ID/sha changes, changed-shot time overlap, native Doctor motion energy, and technical non-stillness component deltas. Both real videos and full song duration are verified independently. Doctor's stasis component may be included as raw measurement, but NEVER becomes a proxy for artistic weakness or a ranking objective.

KEEP, EXPORT, PUBLISH and a future edit are *not* authorized by this experiment. Technical improvement is never claimed.

## In-room operator use

Launch the BAND-IQ 005 Review Room with its previously required verified source inputs, plus a pinned native Blender source path:

    python -m bridge.band_iq_review \
      --cycle /private/cycle.json \
      --selection /private/selection.json \
      --vidmage-record /private/vidmage-film-record.json \
      --vidmage-movie /private/vidmage-original.mp4 \
      --playdeck-receipt /private/playdeck.receipt.json \
      --playdeck-movie /private/playdeck.mp4 \
      --record-dir /private/band-iq-reviews \
      --next-plan /private/native-paper.plan.json \
      --next-cards /private/original-scene-cards.json \
      --next-observation /private/native-toaster-observation.json \
      --next-audio /private/song.wav \
      --next-asset-root /private/source-stills \
      --next-blender-root /private/pinned-haunted-blender \
      --port 8764 --open-browser

The original Blender package must also be available on Python's import path. The laboratory rechecks Git HEAD and the imported module's resolved source path and refuses a moved or wrong donor.

After the creator's second approval produces a third actual MP4, the page exposes **Inspect actual changed windows**. Pressing it prompts for confirmation. The browser sends the explicitly approved observation request, with the same session capability + strict same-origin protection as the original Review Room. Only then are local films rescanned. The page shows the author's original text, actual chosen operation, per-window pixel differences and measured non-stillness deltas. A separate immutable, source-pinned receipt is stored owner-locally.

The request is read-only: no new video is rendered, no paid provider or external network upload is called, and the prior films and choices remain intact.

## CLI for a previously performed revision

    python -m bridge.band_iq_question_lab \
      --cycle /private/cycle.json \
      --selection /private/selection.json \
      --vidmage-record /private/vidmage-film-record.json \
      --vidmage-movie /private/vidmage-original.mp4 \
      --playdeck-receipt /private/playdeck.receipt.json \
      --playdeck-movie /private/playdeck.mp4 \
      --record-dir /private/band-iq-reviews \
      --plan /private/native-paper.plan.json \
      --cards /private/original-scene-cards.json \
      --observation /private/native-toaster-observation.json \
      --audio /private/song.wav \
      --asset-root /private/stills \
      --revision /private/band-iq-005-revisions/revision.json \
      --blender-root /private/pinned-haunted-blender \
      --output-dir /private/question-observations

This creates a content-addressed, create-only JSON observation receipt in the chosen private output folder. A previously written identical receipt is reusable without overwriting it; a conflicting receipt refuses. Reopen independently verifies question, original film and revised film source identities.

## Bounded future questions (NOT executable edits)

1. Which measured picture changes can the creator actually see in the changed time windows?
2. Which performance better expresses the creator's own question, when viewed side-by-side?
3. Which single source, focus or camera variable would the creator explicitly select next?

Every question is proposal-only, requires a human choice and carries execution:false, keep:false and publication:false. It never imports NLP meaning from the artist's original language.

## Automated proof

The band-iq-006 workflow checks exact source pinning, unchanged author evidence, one-shot revision scope, native full-song Blender 008f scanning before and after, independent actual picture frame differences, stasis exclusion, exact source hashes, source-tampering refusal, new question refusal, output and re-openable immutable evidence, and actual local HTTP observation after a real third film. All test assets are synthetic and ephemeral; no private creative data is committed.

## Laws

QUESTION != INSTRUCTION.
EDIT PLAN != ACTUAL PICTURE CHANGE.
PIXEL DELTA != ARTISTIC IMPROVEMENT.
STILLNESS != WEAKNESS.
SOURCE SHA != CONSENT.
TWO NATIVE DOCTOR SCANS != TWO HUMAN REVIEWS.
OBSERVATION != CHOICE.
NEW QUESTION != AUTOMATIC EXECUTION.
SAVED EVIDENCE != PUBLICATION.

Next boundary: a new *human* A/C compare and explicit continuation review. BAND-IQ 006 itself grants neither KEEP nor revision execution.
