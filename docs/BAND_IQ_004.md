# BAND-IQ 004 — human A/B review room

**Experimental local surface**, stacked on BAND-IQ 003. No branch merge, public media upload, hosted deployment or automatic publication.

The actual next step after native VidMage and native Playdeck render two films is not another performance: **a person must watch the results and decide what to do.**

## What this actually builds

- A human-facing responsive browser page containing **two actual locally served MP4s side-by-side**, readable labels, audio A/B choice, synchronous transport controls, and an optional source-hash Inspector.
- A localhost-only Python HTTP service using standard library modules. Bind **127.0.0.1 only**, never 0.0.0.0, and load exactly **two caller-provided original files and evidence records**. It does not expose a project folder browser, arbitrary command runner or remote content loader.
- Bounded MP4 HTTP Range support so the local browser can seek within full-length films. No synthetic thumbnail is substituted for a real playable file.
- Four mutually exclusive explicitly selected outcomes: KEEP VIDMAGE, KEEP PLAYDECK, SCRAPE BOTH, or ANOTHER EXPERIMENT. The latter requires an actual question and does **not** start a render.
- Separate required operator attestation and acknowledgement that a review does not export, spend credits, publish, automatically overwrite media, delete history, perform another experiment, or choose an aesthetic favorite based on the measured technical scores.
- One cryptographically **hash-addressed, create-only, locally stored decision record**, bound to the existing independently verified BAND-IQ 003 paired-real-MP4 comparison, original cycle, both source movies and explicit selected proposal.
- Reopen read-only: refreshing/restarting preserves the first explicit decision from disk. A conflicting later decision about the same pair is refused instead of rewriting the original choice.
- Basic browser CSRF protection via one-session random capability token + exact same-origin check and no CORS; separate source-hash comparisons at commit; no external scripts, tracking, payments or endpoint.
- Test suite exercises actual GET/POST, byte ranges, source mutations, source-receipt mutations, scope boundaries, decision readback, restart, explicit separate next experiment, and one-use refusal.

### Truth boundaries

KEEP is **selected for further local creative continuation**, not Playdeck's own Studio KEEP, not a new master, not a published album video and not an export.

SCRAPE means "neither candidate continues" and does **not** erase source media, prior performance history or source attribution.

ANOTHER EXPERIMENT saves an authored next question but performs nothing. GHoT-style counterfactual automation and reLATTE distribution remain future work.

No model examines the user's face, media or private notes. No remote provider gets source files. The browser loads exactly the two user-supplied local MP4s through its own localhost server.

### Native prerequisites

Use the exact source-pinned BAND-IQ 003 artifacts:
- BAND-IQ source cycle JSON;
- one creator-selected render trial JSON;
- BAND-IQ 002 original VidMage performed-film evidence JSON and its unchanged real MP4;
- BAND-IQ 003 actual Playdeck Remotion receipt JSON and its unchanged real MP4.

BAND-IQ 004 independently calls the BAND-IQ 003 pair comparer again on startup, checking the true source hashes, original creative question and source receipts. It stores/reuses the verified immutable pair receipt in the separate locally selected record directory.

No installed extra dependencies beyond Python 3.12+ are required **once these actual films and prior receipts already exist**.

### Open your local review room

Run from the VidMage repo in the original owning computer/working environment:

    python -m bridge.band_iq_review \
      --cycle /private/source-cycle.json \
      --selection /private/explicit-render-selection.json \
      --vidmage-record /private/vidmage/band-iq-film-evidence/film-record.json \
      --vidmage-movie /private/vidmage/selected-trial.mp4 \
      --playdeck-receipt /private/playdeck/native-playdeck-trial.receipt.json \
      --playdeck-movie /private/playdeck/native-playdeck-trial.mp4 \
      --record-dir /private/band-iq-human-review \
      --port 8764 \
      --open-browser

The process prints a local URL, default http://127.0.0.1:8764/ . A mobile device cannot reach this localhost session running on another computer; a trusted local desktop browser is intended. The user explicitly enters a chosen local review name or unique ID, may leave a written observation, and confirms one of four named outcomes.

The browser is the human-facing review interface; files, hashes and developer anatomy stay in the optional Inspector. The videos are *real* input MP4s, not a mock page, but the surrounding "Start / Bring / Direct / Make / Revise / Export" product UI has **not yet been built**.

### Proof

- python -m unittest -v tests/test_band_iq_review.py
- node --check ui/band_iq_review.js
- python -m unittest -v tests/test_band_iq_playdeck_native.py (with the pinned Playdeck/Blender/Toaster native test environment)

.github/workflows/band-iq-004.yml uses an independent pure suite and also runs the pinned actual *two-film Remotion* synthetic integration inherited from BAND-IQ 003, then reopens and seals a human review from actual native MP4 bytes. None of those synthetic films are user media or copied into source control.

### Custody laws

VIEW != KEEP.
WATCHING TOGETHER != SELECTING EITHER.
DECISION RECORD != SOURCE VIDEO.
ARTISTIC CONTINUATION != EXPORT AUTHORIZATION.
SCRAPE != ERASURE.
NEXT EXPERIMENT QUESTION != EXECUTION.
HASH == IDENTITY CHECK, NOT AUTHOR'S TASTE.
RESTART != ANOTHER CHOICE.
LOOPBACK != REMOTE PUBLISHING.

### Next open frontier

Make this review room reachable from the broader VidMage first-user workflow. Offer **Revise / Compare / Continue**, read explicit human decisions as typed local owner-authorized inputs, and generate a *new, separately approved* run from the author-written next question. Build that only after proving that nothing happens merely because a score is low or a review panel has been opened.
