# Paula Pocket / Little Movie Maker — Vidmage 014

**iPhone-first story → scene → movie planning with local, content-addressed receipts.**

The public source ships with **no actual Paula chat, personal media, screenshots, private names, or accounts**. `paula/index.html` is one self-contained static page (no build step, trackers, CDN, or provider credentials). Mobile Safari is the priority; it also runs on desktop. It is a **planner**, not a hosted Flow Space or video renderer.

## The three steps

1. **My story** — type or paste any story, pick 20 / 60 / 90 seconds and a tone. On iPhone, use the standard keyboard/Dictation if preferred.
2. **My scenes** — get neutral, editable beat cards. They are templates, not automatic semantic extraction. Read each and explicitly approve the actual plan, which records an immutable snapshot receipt.
3. **My movie** — copy an owner-editable prompt to Google Flow Music's **Music videos** workflow, explicitly save a handoff receipt, optionally return with an external link and observations; share project/receipt JSON using iOS native Share Sheet where supported (download fallback).

**Important:** As of 2026-10-13 Google's Flow Music Help says Spaces creation and management are web/PC-only, though Flow Music has an iPhone app. The independent Paula Pocket page avoids making Spaces a mobile dependency. The Flow generation itself is a manual creator action; this repo does not claim provider integration.

## Running

For local desktop testing: `python -m http.server 8000` at repo root, then visit `http://localhost:8000/paula/`. For actual phone use, the static page must be hosted on HTTPS by the owner after reviewing privacy and hosting choices. This branch alone is **not a deployed URL**. Opening raw repository HTML on an iPhone does not guarantee working app storage or Web Crypto; prefer an HTTPS static host. No source file or generation result is automatically uploaded by the page, but HTTPS host access logs are outside this page's control.

The page stores the current project in origin-local browser storage and lets the user explicitly export backup JSON. Safari can purge site data: **export backups to Files/iCloud Drive regularly**. This is not a remote sync service. Save and Share use standard browser features, which vary by iOS version and how the page is opened.

## Receipt contracts

Versioned format: `vidmage/paula-pocket-receipt/v1` with exactly `format`, `event`, `created_at`, `previous_sha256`, `payload`, `sha256`. Each SHA-256 equals the UTF-8 digest of recursively key-sorted, whitespace-free JSON for the other five fields. The `previous_sha256` carries an append-only local chain. Receipts are **content hashes**, not cryptographic signatures or proof of who clicked. Edits after an approved snapshot never mutate its receipt.

| Event | Asserts | DOES NOT assert |
|---|---|---|
| `STORYBOARD_APPROVED` | Creator pressed approval on a saved exact story/scenes snapshot | Film exists |
| `FLOW_HANDOFF_PREPARED` | Exact exported text prepared for Flow Music | Submitted to provider |
| `EXTERNAL_RENDER_REPORTED` | Owner reported the result/link | Output bytes were checked |
| `CREATOR_REVIEW_RECORDED` | Owner recorded notes | Aesthetic ranking or automatic permission |

The app never automatically renders, fetches a provider result, verifies video bytes or publishes media. A full project backup may contain personal story text and must be shared knowingly. Public commits and tests use synthetic material.

## Vidmage consumption

From the repository root:

```sh
python -m paula.receipt paula-receipts.json
python -m paula.receipt paula-receipts.json --write-witness local-paula-intake.json
python -m unittest discover -s tests -p 'test_paula_receipt.py'
```

The first two commands check the chain and event semantics **without touching media, accounts, external URLs, native renderers, or publication**. The optional create-only local witness is `vidmage/paula-import-witness/v1`, with `intake_status=HOLD`. This is a bounded adapter for later source-controlled admission into Vidmage Storytable/filmstrip; it is **not yet a 010 Storytable seal or native render**. Owner authority stays separate.

## Why a branch, not a separate product

This slice can someday hand an admitted story draft to Vidmage's 010 Storytable, 011 Living Filmstrip, 012 Contact Sheet and 013 Candidate Tray. But those experiments currently rely on a private local Python/FFmpeg/Blender/Toaster/Playdeck computer setup and their actual media source hashes. A 20-second prompt sent through an external iPhone app cannot be silently promoted to a local native MP4 receipt. Portable prompt+human-report receipts are the truthful crossing seam.

**DO NOT MERGE/DEPLOY BY DEFAULT.** Review before hosting or linking any private Paula data.
