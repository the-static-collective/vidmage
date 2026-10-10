# VIDMAGE 001 — Architecture

Status: **proposed integration design**, not a claim that VIDMAGE already runs.

## Roles

```
Human creator
  └─ VIDMAGE workbench [Start / Bring / Direct / Make / Revise / Export]
       ├─ local project registry, user choices, explicit consent and job status
       ├─ non-destructive media intake + bounded preview
       └─ local companion (typed jobs, no arbitrary shell)
            ├─ HAUNTED BLENDER [primary film/scene/shot/take engine]
            │    ├─ source-verified pantry
            │    ├─ deterministic six-up / chosen scenes
            │    ├─ 008e full-film deterministic mill
            │    ├─ 008j/008k paper director, cast and dialogue
            │    ├─ 008n/008o/008p narrative/manga-film chain
            │    ├─ MANGALIZE-001..005 material/pixel/presentation chain
            │    └─ FFmpeg render + receipts
            ├─ PLAYDECK [optional cards + Remotion adapter]
            ├─ HAUNTED TOASTER [optional song-first score adapter]
            ├─ GHoT [optional bounded local capability scheduling]
            ├─ text/story publishing input [optional, reviewed source]
            └─ provider connectors [optional / consent + quote + budget]
```

## Authority boundaries

VIDMAGE owns human-facing projects, selection UX, requests, job state, export/release decisions. Blender owns its film and cinematic contracts. Playdeck owns its deck/render contract; Toaster owns score/timeline/KEEP. GHoT owns capability declarations. External providers only deliver *candidate material*, not editorial verdicts.

**Preserve**: source ≠ interpretation ≠ proposal ≠ accepted plan ≠ rendered file ≠ public publication.

## Project format, proposed

```
private-local-project/
  project.json            # project ID, type, title, adapter versions
  material.json           # source hashes, grants, local pointers, retention
  plans/                  # immutable proposals and explicit decisions
  renders/                # preview + final output, sidecar receipts
  edits/                  # versioned revisions; originals intact
  exports/                # release decision + chosen export
```

Runtime material resides on the creator's own computer by default. GitHub only holds code, synthetic fixtures, and public documentation.

## First product mode: local-first

A browser-based workbench + a bounded owner-local companion process; FFmpeg and inspected Blender code run locally. A public marketing site can be hosted separately. A Vercel page alone cannot be assumed to execute local renders, access local files, or perform long-running video encodes.

## Versioned adapter rule

Each donor adapter declares: source repo/ref/SHA; supported input and output schemas; rights/cost gates; deterministic vs provider-generated operations; required runtimes; test fixtures; failure/refusal semantics.

Do not copy source from private repositories and do not assume third-party code is licensed for reuse. Inspect licenses before vendoring any upstream code. Branch identity and test history are carried into each build receipt.

## First delivery gate

A real authorized-media 30–60-second MP4 (H.264, audio if supplied), a second visibly revised render, both output digests and receipts, successful reopen, zero silent public uploads and no surprise paid generation. Synthetic fixture CI alone is not sufficient for human usability.
