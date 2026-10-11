# BAND-IQ 008 — The Living Workbench

**A functioning, responsive, owner-local front door for the existing BAND-IQ 003–007 filmmaking trail.** Experimental and stacked on BAND-IQ 007 PR #11. No public website, automatic merge, release or deployment.

## The creative surface

The workbench is a tactile, moss-and-reel studio interface: analogue perforations, paper/tape hints, deliberately spare typography and **seven truthful doors**:

1. **Bring** — the already existing, source-pinned project's movies and receipts.
2. **Listen** — the original creator-authorized audio, Paper Director plan and scene-card sources, if connected.
3. **Make** — the independently rendered existing VidMage A and native Playdeck B movies.
4. **Wonder** — the actual human A/B review and next question, if any.
5. **Revise** — the separate one-variable, second-authorized BAND-IQ 005 trial, if any.
6. **Notice** — real local Blender 008f and sampled pixel observations, if performed.
7. **Choose** — a **separate A/C human review** of original VidMage A versus the revised VidMage C, not automatically chosen from Doctor scores.

A door's actual status is based on **existing** source media and receipts. The view does not invent an experiment or fabricate progress. The artist's question is preserved verbatim on a paper-tape panel, and an experiment drawer contains each distinct identified revision/observation pairing. If more than one exists, **no newest-or-highest-scoring experiment is automatically preferred**. A person clicks the exact record to enter its independently verified A/C room.

The default face hides long receipt hashes under an optional *Under the floorboards* inspector. Technical evidence remains visible on demand. Buttons link to working local routes; no fake upload forms, credit counters, decorative switches or nonexistent editors.

The visual implementation is bundled HTML/CSS/JS, responsive to mobile widths and reduced-motion preferences. It has no CDN, remote tracking or uploaded artist media.

## What the code actually integrates

All three rooms are served by **one local Python process and one localhost origin**:
- **/** — the new workbench, verified states, restored experiment drawer and original question.
- **/room** — the already working BAND-IQ 004 original A/B reviewer, including the BAND-IQ 005 next-question experiments and explicit BAND-IQ 006 read-only inspection when original local source inputs are configured.
- **/ac/** — the actual BAND-IQ 007 original-vs-revision A/C film reviewer, but only after the operator explicitly chooses an exact existing revision **and its corresponding measured 006 receipt**.

The Workbench uses the real 004 and 007 Python review classes as their route handlers. It does not imitate their video renderers or fabricate backend results. Original A/B source films remain separate from the revised C film. The 007 embedded page uses portable relative URLs so it also continues working as its own standalone localhost service.

The Workbench only discovers project revision JSON files in two **fixed owner-configured private destinations**:
- private 004 record directory / next-trials / band-iq-005-revisions / [SHA].json
- private 004 record directory / question-observations / [SHA].json

It checks each record's cryptographic JSON identity and exact filename. It displays possible matches but **does not trust them as authorized A/C choices until the user selects a specific pair**, at which point BAND-IQ 007 verifies every source film, original artist question, revision, original audio/stills, native observation and history. A mismatched or rehashed forged source is a HOLD, not a different creative interpretation.

Already rendered C movies can also be **resumed explicitly** from the drawer. Their unchanged MP4/source snapshot is independently verified, then BAND-IQ 004 can show the third film again without making another. If the corresponding original 005 editing inputs were not reattached, the reopened film is **display-only**; the application doesn't infer a new render permission or synthesize a new prompt.

No background watcher, remote worker, provider model, file upload, external web browser service, or publication target is created.

## One-time private source-map setup

This experimental branch sits **after films already exist**. It is not yet the unbuilt first-time upload→generative filmmaking pipeline. For an original A/B project already made through BAND-IQ 003–004, make a private local project profile **once**:

    python -m bridge.band_iq_workbench init \
      --cycle /private/film-cycle.json \
      --selection /private/render-selection.json \
      --vidmage-record /private/vidmage-film-record.json \
      --vidmage-movie /private/vidmage-original.mp4 \
      --playdeck-receipt /private/native-playdeck.receipt.json \
      --playdeck-movie /private/playdeck.mp4 \
      --record-dir /private/band-iq-review \
      --output /private/vidmage-workbench.json

The init command opens and verifies the actual independently rendered A/B comparison before saving the profile. The map is **create-only and owner-readable** on disk (mode 0600) and records absolute local paths, not media bytes. **Keep it private.** Never check it into a public Git repository: filenames, paths and creator questions can identify private material.

For projects with BAND-IQ 005 next questions and 006 measurements, append **all five** original project inputs when initializing the profile:

    --next-plan /private/native-blender-paper.plan.json
    --next-cards /private/original-editor-scene-cards.json
    --next-observation /private/native-toaster-audio-observation.json
    --next-audio /private/song.wav
    --next-asset-root /private/owned-stills

Optionally also append:

    --blender-root /private/exact-pinned-haunted-blender
    --ac-record-dir /private/band-iq-007-human-decisions

The Blender path must be the source-pinned native Blender checkout required by BAND-IQ 006. It will only be executed on a **separate explicitly requested observation** in the 004 film room, never on merely opening the dashboard.

The integrated experiment drawer currently reads the default private BAND-IQ 005/006 output subdirectories under --record-dir. If previous CLI output was saved elsewhere, put the existing JSON receipts into those private expected directories by their SHA filename, or keep using the standalone reviewer with explicit source paths. Do not alter media or rewrite original receipt content.

## Subsequent sessions: one command

    python -m bridge.band_iq_workbench open \
      --project /private/vidmage-workbench.json \
      --port 8766 \
      --open-browser

The local URL is **http://127.0.0.1:8766/**. No account, upload, GitHub login or hosted service needed. An earlier signed decision is simply read back; it isn't performed again. If multiple measured revisions exist, select the particular experiment you want to consider. If one lacks measurement, select *Resume this local trial* to watch C (without a render) and, when original source inputs/native Blender are connected, optionally request a new read-only observation.

The profile, original MP4s, separate source JSONs, film trials, measurements and human decisions stay in their original owner-local directories. The application uses **one** loopback-origin session capability for selecting a source pair and delegates the original human approval steps to their own existing explicit session tokens.

## Browser routes and trust boundaries

GET:
- /, /workbench.js, /workbench.css: bundled static workbench.
- /api/workbench/status: verified seven-door state and candidate *identities*, not approval.
- /room, /api/context, /api/next/questions, /review.js, /review.css and original media routes: existing 004/005/006 room.
- /ac/, /ac/api/context, /ac/ac-review.js, /ac/ac-review.css, /ac/review.css and /ac/media/a|c: independently selected real 007 A/C room.

POST:
- /api/workbench/select: explicit SHA pair choice, same-origin + random token, no arbitrary file paths.
- /api/workbench/restore: explicit known 005 revision identity, recheck unchanged source bytes; no execution.
- /api/decision, /api/next/execute, /api/next/observe: the original 004/005/006 human action gates, unchanged.
- /ac/api/decision: a **separate** A/C decision after exact pair selection; does not expose /ac/api/next/execute or any other old execution route.

All endpoints bind only 127.0.0.1, reject unknown browser file paths, have no cross-origin allowances and reuse restrictive content security headers. Every POST affecting user choices requires an explicit supported form, session capability and exact same origin. A malicious, mismatched, stale or modified source is refused; no automatic fallback to an unrelated source.

### Truth boundaries

- SELECT AN EXPERIMENT != CREATIVE KEEP.
- MEASURED CHANGE != BETTER FILM.
- QUESTION != COMMAND.
- REOPEN != RERENDER.
- TWO FILMS != AUTOMATIC PICK.
- OLD HUMAN REVIEW != NEW HUMAN REVIEW.
- BRINGING A SOURCE != EXPORTING IT.
- CONTINUE != PUBLISH.
- PROJECT PATH MAP != PERMISSION TO ACCESS OTHER FILES.
- STILLNESS != WEAKNESS.

## Executable proof

New tests in tests/test_band_iq_workbench.py validate the project profile, source-derived progress, candidate counts, restart/reopen with old films unchanged, explicit SHA source pairing, a forged observation refusal (including rehashed input), same-origin protected workbench POSTs, one-port existing 004 plus 007 film byte-range playback and fresh author A/C choice. Pure UI syntax checks validate all bundled source scripts. The separate source-pinned native CI in .github/workflows/band-iq-008.yml reruns actual synthetic Toaster/Blender/Playdeck/VidMage film performances and earlier BAND-IQ A/B→question→C→Doctor→A/C human custody.

No synthetic test media are committed to the branch.

## Open frontier

The next real upgrade is **an on-ramp for a genuinely new, nontechnical person**: import one existing song and a few owned images, inspect permissions, begin first local paper/story planning and render initial A/B without assembling those initial movie receipts by hand. That upload/source intake and full render workflow are **not yet delivered** by BAND-IQ 008; its current one-door integration begins with source-pinned work already made in 003–007.
