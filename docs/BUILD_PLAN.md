# VIDMAGE — Grand Smash / bounded build plan

Scope: shipping one real independent creator video studio. Mainline is **Blender-first**, guided by source-branch code and tested exact heads. No bulk history rewriting.

## P0 — Canon the donors, not just Git default branches

- Keep [the 60-ref Blender inventory](BLENDER_BRANCHES.md) and [proof ledger](PROOF_LEDGER.md).
- Clone/pin `integration/mangalize-005-presentation-ground` at `cf0256a49ac8aa879cf2a044847d248177fcfad9` as a composite **inspection candidate**; no implied release canon.
- Inspect ancestry versus independent sibling branches (including 005 GHoT Compost Adapter and separate experimental lineages). Record `adopt-in-place / adapter / port / archive / unresolved`.
- Repeat 441-test suite under pinned Python/Pillow/FFmpeg versions; confirm real media smoke with synthetic assets.
- License audit: code and input media may be public but not necessarily unrestricted for reuse.
- **Exit:** a machine-readable, versioned donor manifest and unmodified upstream tests green at selected heads.

## P1 — The film is complete before the studio is fancy

- Build a bounded *local* VIDMAGE companion around an exact Blender executor; no arbitrary shell strings accepted from browser.
- Intake and hash approved photos/video/audio; originals read-only. Local project manifest and explicit use rights.
- Use actual 008e zero-dollar `zero_dollar_cli smash` pipeline to make one whole playable cut.
- Return `mp4 + plan + render receipt + source hashes + duration and cost`; verify with ffprobe + SHA-256.
- **Exit:** one synthetic and one authorized real 30–60-second movie, zero external generation, no private files in Git.

## P2 — A human controls it

- Borrow **008a visual cockpit** and **008b auto-crossings** as human-flow evidence. Keep `GROW / KEEP / AWAKEN / PLAY` authority and translate into creator-facing verbs.
- Browser control: Start, Bring, Direct, Make, Revise, Export. Hide IDs, score anatomy and Git details by default.
- Show a first complete cut, allow a segment to be deliberately changed, render a second cut and reopen project from disk.
- Distinguish focus/preview vs KEEP; failed render vs finished media.
- **Exit:** cold-start first-user witness with no command-line operation.

## P3 — Story, cast and paper-stage films

- Wire 008f weakest-window improvements, 008g cutouts, 008h parts, 008i moving inserts, 008j Paper Director, 008k ensemble dialogue; all by exact-head adapters.
- Use 008n narrative custody and 008o/008p moving, audible, source-pixel manga proofs for *Story* mode. Respect MANGALIZE permissions; static page execution does not itself authorize motion/print/publication.
- Use the same film project and receipts, not a second hidden animation source of truth.
- **Exit:** 2–4 character short story film with dialogue cues, proper speaker/reaction geometry, second editable cut.

## P4 — Wider creative production

- Adapters for Playdeck (Remotion cards), Toaster (music-first timeline), GHoT (capability scheduling), and book/story publishing (selected legal source).
- Optional external video models: explicit cost quotes, human pre-approval, media upload consent, local-only fallback, and receipt for actual provider work.
- Formats: 16:9, 9:16, captioned, trailer/teaser, series templates. Publish remains a separate user decision.
- **Exit:** independent provider failures do not destroy local editability.

## Required QA throughout

- Source bytes unchanged; project opens after restart.
- A proposal never silently becomes an authorized render or a publication.
- No surprise network transfer, generated voice likeness, paid credits, or insecure media path traversal.
- Source, branch and exact donor SHA cited in integration receipt.
- Actual FFmpeg output and inspectable video/audio/duration, not merely a mocked UI.
- Donor test suite results and VIDMAGE integration tests reported separately.
- No claim of a deployed AAA app before successful independent human use.

## First pull requests after this planning PR

1. `P0: create donor lockfile + reproducible Blender test harness`.
2. `P1: local deterministic end-to-end film + receipt adapter`.
3. `P2: small VIDMAGE cockpit over *real* local render state`.

Prefer a complete narrow crossing over disconnected feature islands.
