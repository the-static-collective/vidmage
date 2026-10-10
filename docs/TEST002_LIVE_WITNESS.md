# VIDMAGE — Native Blender live Test 002 (local media)

**Observation:** The first real creator-media test ran the existing Haunted Blender **008e Zero-Dollar Film Mill** and **008f Weakest Window Doctor**, pinned to source SHA `cf0256a49ac8aa879cf2a044847d248177fcfad9`. Creator media did **not** leave the local machine or enter this public GitHub repository.

## What was actually tested
- Source: 8 authorized still images prepared locally into eight short silent MP4 ingredients, and one ~184.344-second audio track.
- 008e: deterministic entire-song plan, **24** slugs, **11** actual recipe names, **8** distinct source ingredients, provider credits/spend **0**.
- Observed final output: **184.32 seconds**, H.264 640×360 at 12fps, stereo AAC, 99.987% duration coverage. Actual encoded output hash matched the 008e render receipt.
- Targeted native 008e unit suite **5/5 pass**. 008f unit suite **5/5 pass**.
- 008f prescription: **3** local recipe changes, full trial rerender. Native mean-weakness heuristic **0.437742 → 0.436809** (tiny improvement; this metric is not an aesthetic judgment).

## Newly witnessed upstream failure
Unmodified 008e render failed at the third segment using the `reverse` filter, with FFmpeg subprocess killed by SIGKILL 9. The native builder combined `-stream_loop -1` and `reverse` without a bounded input EOF; both `-t` flags were after `-i`. This can require infinite reverse buffering. Moving the input duration `-t` before `-i` (while retaining the output `-t`) allowed a successful full render. **This is a local test-only modification and not a claim that the upstream branch has been fixed.**

See upstream [Haunted Blender issue #69](https://github.com/the-static-collective/the-haunted-blender/issues/69). Adversarial synthetic regression coverage and review are required.

## Human observation: coverage is not direction
The native 008e result is recognizably a rearranged still-image montage with recipe-level variations. It does **not** preserve intended verse/chorus narrative, lyric-specific scene placement, or a selected final-cover placement. The first film was full length, but the current candidate is not a finished directed music video. There was no invented moving character animation or parallax.

## Next proper organ, not another generic motion filter
Use existing Blender `008j Paper Director` and `008n narrative-particular → accepted staging`, with optional Toaster score/timeline adapters, to test **intentional edit order and bounded camera behavior**. First gate: supply exactly edited sections and their actual soundtrack timing; verify the user can override the chosen moments and retain the same project history.

Keep the proposed [optional multi-pass kinetic camera layer](https://github.com/the-static-collective/vidmage/issues/2) **deferred** until a grounded native directed pass exists.

## Honesty / privacy
This document records public **result metadata only**, not image bytes, audio bytes, original filenames, private links, personal biographies, unlicensed media or provider credentials. Rendered media, receipt files and exact local review artifacts remain with the creator, not published. Actual user media results are not interchangeable with synthetic tests, and a passing upstream test does not establish a production-ready VIDMAGE application.
