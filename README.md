# VIDMAGE

**A creator-first video studio, powered by the Static Collective's existing filmmaking experiments.**

**Status:** Public project home / integration planning. **Not** a deployed video application yet.

## The promise

**BRING → DIRECT → MAKE → FINISH → RETURN**

Bring a song, images, a story, a voice recording, or authorized clips. Get a playable video, choose what stays, revise a scene, and export a finished file. The project remains reopenable. Generated ideas never override human decisions.

VIDMAGE aims to let ordinary creators make film without learning Python, FFmpeg, Git branches, or video-model APIs. The first test user is a nontechnical independent creative producer; usability and accessible workflows take precedence over technical spectacle.

## Where the engine comes from

The primary story/film production donor is [Haunted Blender](https://github.com/the-static-collective/the-haunted-blender), **including its tested, unmerged branches**. Its default branch alone is not an honest inventory of this project. [Playdeck](https://github.com/the-static-collective/playdeck) is a complementary deck/Remotion performance engine; [Haunted Toaster](https://github.com/the-static-collective/the-haunted-toaster) contributes the song-first candidate/render lineage. Other adapters may arrive behind explicit interfaces.

The source repositories retain ownership of their code and contracts. VIDMAGE is an integrating product, not a mass-merge or a claim that every experiment is production-ready.

## First executable target

A person supplies authorized local images/clips and optional audio, receives a **complete playable MP4** from deterministic local rendering, makes **one observable revision** to one section, and exports a second MP4 with attributable receipts. The source files remain unmodified. Synthetic fixtures and repeatable tests are required.

## Public repository boundaries

Only source code, synthetic fixtures, public evidence, and reviewed documentation belong here. Never commit personal media, customer data, private documents, API tokens, provider credentials, downloaded account sessions, EXIF location metadata, or full render corpora.

No paid generation, provider upload, public sharing, publication, or voice/likeness use without explicit user authorization and applicable rights.

## Development

Read the proposed implementation packet:

- [Build plan](docs/BUILD_PLAN.md) — complete movie first, cockpit second, integrations after
- [Architecture](docs/ARCHITECTURE.md) — Blender first, typed donor adapters
- [Blender branches](docs/BLENDER_BRANCHES.md) — all 60 refs, not just `main`
- [Exact-head proof ledger](docs/PROOF_LEDGER.md) — tested source and render evidence
- [Donor atlas](docs/DONOR_ATLAS.md) — reusable neighboring systems
- [First-user acceptance](docs/FIRST_USE.md) — one full editable video
- [BAND-IQ 001](docs/BAND_IQ_001.md) — evidence → six cinematic questions → explicitly selected native experiments → comparison → replayable local memory; quietness is protected
- [BAND-IQ 002](docs/BAND_IQ_002.md) — human-selected proposal becomes a real trial movie with native Blender parts/material custody, actual Toaster audio, and independent before/after Doctor scans
- [BAND-IQ 003](docs/BAND_IQ_003.md) — actual source-pinned native Playdeck Remotion renderer and a separately witnessed comparison against VidMage's selected-window movie
- [BAND-IQ 004](docs/BAND_IQ_004.md) — local two-film review room where a person explicitly selects KEEP A, KEEP B, SCRAPE BOTH or a new experiment question; source films remain immutable
- [BAND-IQ 005](docs/BAND_IQ_005.md) — the author's verbatim next question becomes three bounded test proposals; a second human authorization can perform one local third film and preserve an editable, reopenable revision
- [BAND-IQ 006](docs/BAND_IQ_006.md) — native Blender rescans the actual old/revised movies against their proper source cards, independently measures picture differences, and returns human-only next questions without ranking art
- [BAND-IQ 007](docs/BAND_IQ_007.md) — a separate local A/C review room where the creator watches original versus revision and signs an immutable follow-up continuation choice, without rewriting source history
- [BAND-IQ 008](docs/BAND_IQ_008.md) — a tactile, single-origin owner-local seven-door workbench combining original/revised film rooms, real human questions and restartable source-verified experiment navigation
- [BAND-IQ 009](docs/BAND_IQ_009.md) — the creator-facing first song and owned-images porch, with explicit local permissions, native Toaster/Blender preparation, independently approved actual VidMage/Playdeck A/B renders and automatic handoff to the living workbench
- [BAND-IQ 010](docs/BAND_IQ_010.md) — the human Storytable: hear the actual song, assign owned photos to each native shot, choose per-occurrence framing/text protection, then seal the exact source before the first A/B films
- [BAND-IQ 011](docs/BAND_IQ_011.md) — the Living Filmstrip: source-real, song-timed pre-film raster samples from sealed authored cards, without generating a movie or making a creative selection
- [BAND-IQ 012](docs/BAND_IQ_012.md) — the Contact Sheet: before sealing the Storytable, compare real current-versus-candidate local raster frames for one song window and explicitly apply the alternate only to the unsealed draft
- [BAND-IQ 013](docs/BAND_IQ_013.md) — Candidate Tray × Grab/Cross Bits: hold four reversible multi-shot story possibilities, borrow traceable owned-image rectangles into shots, and make real VidMage/Playdeck films from a separately sealed composition

The pinned upstream SHA list lives in [donors.lock.json](donors.lock.json). Run `npm test` and `npm run verify:donors` (Node 22+) to validate its structure offline. These tests validate metadata shape, **not** upstream feature behavior or user-level filmmaking.

Proposed work proceeds on a reviewable branch; no merge or deployment is implied by a passing test or a draft pull request.

This repo is the **approved public home**: `the-static-collective/vidmage`.
