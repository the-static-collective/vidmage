# VIDMAGE — instructions for contributors and coding agents

## Product goal
Make a real, revisable video from creator-authorized material. Start with a nontechnical maker's experience rather than a machinery dashboard. The first acceptance test is: **make a movie → change one scene → export a second movie → reopen the project**.

## Correct repository
The approved public home is `the-static-collective/vidmage`. Do not redirect work to `thestaticcollective/vidmage` or write to another lookalike. The two owners are different.

## Source reality
- **Branch code counts. Tests count.** Review all upstream relevant branches and their exact commit/test history, not only `main`.
- Haunted Blender is the primary story-first filmmaking donor. In particular inspect `integration/mangalize-005-presentation-ground`, the `franken-blender-008*` series, and independent experimental siblings.
- Historical donor proof is valid evidence for that exact head and environment; it does not by itself prove a new VIDMAGE integration or product acceptance.
- Preserve source project contracts and full provenance. Prefer pinned imports and typed adapters over bulk merging an entire branch stack.
- Build a living donor ledger with source repo, branch, exact SHA, run, observed capability, dependent software, integration disposition and current owner.

## Explicit constraints
- Public repo: source code + synthetic fixtures + reviewed documentation only. Never import private repo content, personal/third-party media, customer data, contact details, tokens, large rendered videos or location-bearing EXIF.
- Before reusing donor code, verify applicable license/permissions; publicly viewable code is not automatically freely relicensable.
- User controls creative selection, paid generation, external upload, use of voices/faces, export and publication. Viewing is not selection; proposal is not execution; render is not publication.
- Preserve source bytes and reversible editing; receipts report actual results and failures, not inferred successes.
- Model or plugin availability does not imply cost allowance or authority.
- Never execute arbitrary commands accepted from a remote user. Local companion interface exposes bounded typed job handlers only.
- No background provider login scraping or session extraction.

## Build procedure
1. Inspect branch and PR ancestry; pin chosen donor heads.
2. Define a narrow, testable slice and failure behavior.
3. Implement against synthetic media.
4. Run existing donor tests unmodified and VIDMAGE integration tests separately.
5. Produce a cold-run MP4 and receipts with verified output hash, runtime versions, actual duration and source lineage.
6. Test edit-and-rerender, project reopen, cancel/failure, no-cost default, and denied public upload.
7. Prepare reviewable PR with commands and observed results. No automatic merge, release or deployment.

## First user interface
Show **Start / Bring / Direct / Make / Revise / Export**. Internals (branches, hashes, anatomy, provider routing) belong in an optional Inspector. UI copy must distinguish available, proposed, running, blocked and complete states.
