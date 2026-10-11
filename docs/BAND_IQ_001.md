# BAND-IQ 001 — Evidence to the next experiment

BAND, not BELT. Six ways to see; one chosen experiment at a time.

Status: executable experimental VIDMAGE integration, stacked on VIDMAGE CROSS-001 at exact commit 223190e7294197532cdfebb598ae8d85f8273c7e. Nothing merged, deployed, released, or published. No upstream donor changed.

## The six-stage instrument

PERCEIVE → RELATE → IMAGINE → EXPERIMENT → COMPARE → REMEMBER.

- PERCEIVE: a genuine Blender 008f Doctor scan of a full actual local MP4; optionally the existing VIDMAGE CROSS-001 / native Toaster L BRANCH audio energy and transient observations. No invented timed lyrics, semantics, or source meanings.
- RELATE: typed, exact-source references and operator-attested deliberate-stillness or protected-scene windows. No inference of object identity, ownership or creative approval from a mask, waveform or score.
- IMAGINE: six explicit Playdeck Studio 011 cinematic grammars projected into BAND-IQ proposals. Proposals never turn into rendered shots by themselves.
- EXPERIMENT: an explicit, separately attested native Blender action under a pinned checkout. Original media untouched. No paid provider and no uploading media.
- COMPARE: match two independently observed native Doctor reports to same song coverage, inspect genuine technical deltas excluding artistic stillness, refuse unchanged source media and lost coverage. No automatic KEEP.
- REMEMBER: locally stored SHA-256 create-only cycles, trial receipts and optional exact-prior-cycle ancestry. Source identity changes require another explicit crossing.

## Donor register and actual scope

1. Blender 008f / Weakest Window Doctor: donor branch SHA 363e1ddcb22570b82e3df5b07008c0a2a79f1c1c. Real gated native scan integration.
2. Blender 008h / Parts Harvester: donor SHA 9bdd378b98001770af1191c01ae93e7938265bf3. Real gated native harvest integration.
3. Blender 008j / Paper Director: donor SHA 070d8034e11052f7e84588e19e36f452c862a772. Real gated native already-approved-plan render entry.
4. Blender 008l / Material Surfaces: donor SHA a39d6c3be8197b38b06c2f45fb323e4ef8b4f279. Real gated native materialization.
5. Composite Blender source: cf0256a49ac8aa879cf2a044847d248177fcfad9. Verified Git HEAD plus actual imported package path required. Inherits the preceding 008f/h/j/l code.
6. Playdeck Studio 011: 012186fd67f4c4ef1c6591fc5e29cb559b5a80d0. Cinematic grammar vocabulary only; direct Playdeck runtime integration is a **later stage**, not simulated as native.
7. VIDMAGE CROSS-001: 223190e7294197532cdfebb598ae8d85f8273c7e. Existing real native audio-to-Blender crossing, independently tested before BAND-IQ; no claimed video selected for BAND-IQ.
8. Toaster native L BRANCH: 3652c2a96b6b287cda316d1c92daadf7c7417eaf. Existing VIDMAGE source pin.
9. GHoT RIFF-RAFT-005: 4dc0e33484d998043e0955c016a3984d8f75e4ef. Next-question experiment design inspiration only, not imported.
10. GHoT 030: b01758bee55d66d699160715ec377b45f7589707. Source-pinned one-use owner-work design inspiration, not BAND-IQ actuation.

External options **not installed or imported**: SAM 3.1, Depth Anything 3, PySceneDetect and VMAF. Model/copyright, compute and accuracy checks and human local permission are future gates.

## Operator workflow

Use Python 3.12+, FFmpeg/FFprobe, Pillow, and a local git checkout of Blender at composite pin above. Set PYTHONPATH to both VIDMAGE root and exact pinned Blender root. All source media, user notes and outputs remain owner-local.

**1. Create an explicit selection file** at a private path (e.g. /private/scan.selection.json):

    {
      "schema": "vidmage/band-iq-local-selection/v1",
      "operation": "scan-008f",
      "sourceRights": "creator-authorized",
      "operatorAttestationId": "explicit-creator-action-001",
      "allowLocalExecution": true,
      "allowPaidProviders": false,
      "allowNetworkUpload": false
    }

**2. Native Doctor scan** a locally held full MP4 and corresponding valid 008e full-coverage plan:

    python -m bridge.band_iq_donors scan-008f \
      --selection /private/scan.selection.json \
      --blender-root /path/to/pinned-blender \
      --source /private/current-cut.mp4 \
      --plan /private/current-cut.plan.json \
      --output /private/band-iq/scan

The result is /private/band-iq/scan/doctor.json containing an independently checked 008f report, its SHA, and actual source media SHA. The wrapper produces a separate native-adapter record.

**3. Optionally author artist window annotations** with the exact source hash and existing window IDs. Supported kinds: deliberate-stillness, protected-scene, motion-review-authorized. Each annotation also has an operatorAttestationId. All annotation data is explicit, no automated quietness or intent inference.

**4. Assemble a typed BAND-IQ input**:

    python -m bridge.band_iq assemble \
      /private/band-iq/scan/doctor.json \
      /private/band-iq/input.json \
      --audio /private/toaster-observation.json \
      --artist /private/artist-annotations.json

Omit either option when that local evidence does not exist. A modified Doctor envelope refuses; an untimed lyric sheet never asserts vocal salience.

**5. Imagine six questions, content-addressed**:

    python -m bridge.band_iq propose \
      /private/band-iq/input.json \
      /private/band-iq/cycles

Produces six grammars named landscape/survey, architecture/hinge-orbit, organism/pulse-dolly, sigil/snap-frame, weather/wind-eye, dimensional-space/parallax-orbit. They are typed proposals, not executed Playdeck instructions. The highest-ranked meaningful **non-stillness** measurement gets an optional experiment target; if no such target exists, HOLD is emitted.

**6. Explicitly select an experiment**, if desired. Run:

    python -m bridge.band_iq_donors capabilities

The four real supported donor verbs are scan-008f, harvest-008h, direct-008j, and material-008l, each requiring a newly authored explicit selection document naming its operation, no paid work or uploads, a pinned donor root, a real local source and a create-only output. Native 008j accepts an existing native approved paper plan; BAND-IQ does not pretend one of its six speculative view questions is already such a plan. Blender's separate 008f local Level-1 trial pipeline exists upstream but is not automatically invoked.

**7. Compare two independent actual scans**. Unwrap native Doctor report JSON values from the scan envelopes and provide the original report, a second report from a separately rendered edited MP4, and the saved cycle:

    python -m bridge.band_iq compare \
      /private/band-iq/cycles/<cycle-sha>.json \
      /private/band-iq/scan/before-native-report.json \
      /private/band-iq/trial/after-native-report.json \
      /private/band-iq/comparisons

A comparison enforces same measured windows, no loss of coverage, distinct MP4 source bytes and matching earlier report identity. Numeric comparison is diagnostic only. An optional --human-review file records KEEP / SCRAPE / HOLD with explicit operator attestation; neither numeric improvement nor this API publishes a film.

**8. Preserve the history.** Cycle and trial records are create-only and content-addressed. A new cycle may supply --previous /path/to/cycle.json, but only for the same exact source identity. There is no silent writing to Memento, FreeGraph or other repos.

## Stillness is not error

008f observes a stasis dimension. BAND-IQ deliberately strips this component out of **both automatic candidate ranking and its quantitative trial-improvement metric**. Motionlessness alone can never cause a proposed change or automatic acclaim. Author-attested protection additionally prevents pursuing a quiet passage even when its technical repetition is high. An operator can explicitly request motion-review on a particular window without enabling automatic work.

STILLNESS != WEAKNESS.
STATIC != INCORRECT.
SCORE != TASTE.
AUDIO ENERGY != LYRIC TIMING.
SOURCE != PROPOSAL.
PROPOSAL != EXECUTION.
TRIAL != KEEP.
VIEW != WORLD.
RECEIPT != PUBLICATION.

## Proof gates and incompleteness

- Pure Python unittest covers six distinct grammmars, protection, falsified evidence refusal, claim/authority refusals, changed media, coverage loss, technical-vs-artistic score, predecessor integrity and write-once custody.
- GitHub Actions builds from exact composite Blender SHA and tests a genuine native 008f scan against an actual synthetic FFmpeg MP4. Synthetic media only; no real user inputs or videos uploaded.
- This first BAND-IQ PR is an executable **local instrument**, not a VidMage GUI or a turnkey complete human-created film. It has not directly operated the Playdeck Remotion renderer, auto-selected source footage, or achieved a full personally reviewed experiment-to-fourth-film product witness. The human-first VIDMAGE Start / Bring / Direct / Make / Revise / Export interface remains separately required.
- Optional SAM, Depth, PySceneDetect and VMAF adoption requires its own provenance, license, local resources and gating.

Goal of subsequent slice: actual first complete creator-controlled before/after film, owned 008h parts reused as 008j inserts and 008l surfaces, Playdeck six-way native film trial, source-pinned evidence, and an author-selected next question without auto-KEEP.
