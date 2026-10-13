# Paula Pocket 014 — mobile-first story-to-film receipt bridge

**Status:** Experimental Vidmage branch. **Not deployed or merged.** No real Paula material is committed.

## What Paula actually sees
Open `paula/index.html` on a normal HTTPS static host in iPhone Safari.

1. **Story:** type/dictate the idea; choose 20, 60, or 90 seconds and a Christian/family/hopeful mood.
2. **Scenes:** neutral starter beat cards, deliberately editable by Paula. They do not pretend to be AI story extraction. Explicit "These scenes are mine" records a hashed snapshot.
3. **Movie:** copy a complete prompt to Google Flow Music's *Music videos* workflow. Explicitly record handoff, return with a link or note, and export the project/receipt chain to Files using iOS Share Sheet when supported.

This source has no tracking, CDN, provider token, personal media, remote account linkage, or silent uploads. Storage is browser-local, and Safari can evict it. **Back up to Files often**. A static HTTPS host may log page visits under its own policies. Phone usability requires human testing on a real iPhone before calling it field-proven.

**Product boundary:** According to Google Flow Music Help as checked 2026-10-13, Flow Music *Spaces* creation is web/PC-only. Paula Pocket is intentionally independent of Spaces and redirects to the music-video tool for rendering. It does not assert direct provider API access.

## Receipts and Vidmage intake

Format: `vidmage/paula-pocket-receipt/v1`. The receipt has six exact fields: `format`, `event`, `created_at`, `previous_sha256`, `payload`, `sha256`. The SHA-256 digest covers canonical, recursively key-sorted compact UTF-8 JSON of the other fields; `previous_sha256` chains events.

| Event | Truth preserved | Not proven |
|---|---|---|
| `STORYBOARD_APPROVED` | The particular storyboard Paula clicked to approve | Render |
| `FLOW_HANDOFF_PREPARED` | Exact directions prepared for provider | Provider received/acted |
| `EXTERNAL_RENDER_REPORTED` | Creator reported a link or an attempt | Verified video bytes |
| `CREATOR_REVIEW_RECORDED` | Creator's own remarks | Objective ranking / acceptance |

These are **tamper-evident content hashes, not signatures**. A fabricated chain can still contain fabricated claims. Neither browser-local state nor a provider link proves creator identity, video generation, rights, or source-media equivalence.

Vidmage's import checker is read-only:

```sh
python -m paula.receipt paula-receipts.json
python -m paula.receipt paula-receipts.json --witness my-private-paula-intake.json
python -m unittest discover -s tests -p 'test_paula_receipt.py'
```

It validates JSON event structure, content hashes, predecessor chain, source project identity and forbidden false media claims. It emits an explicit `vidmage/paula-import-witness/v1` with `intake_status=HOLD`, never automatically running native renderers or converting a reported Flow Music URL into a verified MP4. Witness creation is opt-in and create-only.

## Why it belongs on a Vidmage branch

Base ancestry is `experiment/band-iq-013-candidate-tray-cross-bits`, retaining Vidmage Storytable 010, Living Filmstrip 011, Contact Sheet 012, and Candidate Tray/Grab-Cross 013. Those local native tools still require a real desktop preparation and actual source media. Paula Pocket is a separate **mobile surface and portable proposed-input organ**. A future bounded importer can map *approved* scene plans into an editable 010 Storytable **only after owner admission**; no current claim of source photo/MP4 verification or direct Flow Music rendering.

The human holds the authority: STORY != SHOT; SCENE APPROVAL != RENDER; EXTERNAL LINK != VERIFIED FILM; IMPORT != ADMISSION; HOLD != KEEP; KEEP != PUBLICATION.

### Source references
- Flow Music Spaces limits: https://support.google.com/flow/answer/17083802
- Flow Music iPhone: https://support.google.com/flow/answer/17083868?co=GENIE.Platform%3DiOS
- Vidmage parent experiment: https://github.com/the-static-collective/vidmage/pull/18

**Do not auto-merge, deploy, spend provider credits, publish media, or commit Paula's private story/screenshot.**