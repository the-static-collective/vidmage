# BAND-IQ 012 — The Contact Sheet

**Status: experimental, functioning source-raster A/B comparison for an UNSEALED Storytable.** Stacked directly on BAND-IQ 011 PR #15. No merge, deployment, provider calls, public publication or autonomous film selections.

## The odd little creative instrument

The creator is already in the local Front Porch. They have brought a real owned song and pictures, granted local-use permission, and asked native Toaster and Blender to create the factual song-timed paper shot plan.

Before **Seal my Storytable**, each song window now has a second tabletop:

- **THIS — your current unsealed draft:** the photograph currently chosen for that song shot, with its actual current focus and protected-text setting.
- **THAT — another possibility:** independently choose another already-owned picture, horizontal/vertical focal point and protected-text setting. The current draft is not edited while trying this.
- **Show me both possibilities:** the local VidMage raster engine samples the SAME actual song shot at 12%, 50% and 88% of its available native 12-fps frames for each side. Six authentic sourced JPEGs appear side by side, with the exact song timestamp. Selecting a frame seeks the local song to that time.
- **Apply THAT to my draft:** only after a human click and confirmation, changes the in-memory **unsealed browser draft** for that one shot occurrence. The 010 human *Seal my Storytable* remains an entirely different, later explicit operation.
- **Leave my draft alone:** discards the local comparison on screen without affecting the draft. Changing candidate controls or navigating to another shot also invalidates the comparison.

The rendered preview images are the actual output of the existing \`scene_card_film.frame_for\`, with the same prepared owned picture bytes, selected focus/text protection and native Toaster energy. These are **not** AI guesses, a finished movie, a Playdeck composition, a kinetic pulse or a cinematic-lens performance. The original provisional cards and owner's uploaded images are untouched. Different sample bytes are factual observations, not an aesthetic score.

### Privacy and continuity

BAND-IQ 012 deliberately does **not** create a permanent comparison folder, native film receipt, story receipt, edit history, timestamp-based identity or remotely stored media. Each six-frame comparison is held only in the local Front Porch server's Python memory.

- The comparison result has a canonical JSON SHA-256 identity binding the exact native shot/time, old provisional source plan, prepared photo/audio/Toaster source hashes, both **specified** alternative treatments and all six generated JPEG hashes/timestamps.
- Local reads are fixed routes \`/api/porch/contact/frame/<comparisonSha256>/<left|right>/<0|1|2>\`; there is no browser-supplied filename or path. Each GET verifies the exact current session comparison and returned image bytes. A newer comparison supersedes the previous one, and sealing the Storytable invalidates the entire preview immediately. Restarting the server forgets ephemeral previews.
- A separate same-origin, exact session-capability \`POST /api/porch/contact/compare\` requires precisely one native shot ID, one current-source choice, one alternate-source choice, bounded focus coordinates and all execution/release flags explicitly false.
- The backend checks the 009 prepared native receipt, the actual original normalized song bytes, owned picture SHAs, original unmodified Paper Director shot plan and signed Toaster observation. Requests for unowned images, unknown shots, out-of-range focus, corrupt original files or modified paper sources are HOLD.
- After a Storytable has been sealed, comparison requests are refused; the 010 seal retains complete and separate authority. Merely inspecting or comparing does **not** authorize adding a shot to the saved Storytable or selecting a finished film.

The baseline named **THIS** is the current *browser draft*, **not necessarily the original paper proposal**. This matters because an artist may have already changed the scene order, picked a different photo or shifted framing without sealing. The backend makes no assertion about a draft it cannot see: the browser submits the exact explicit owner-visible two candidates. **Apply** checks that the draft and alternative still match the comparison; no fallback, auto selection or invisible save occurs.

## Real local user path

Same pinned native setup and local startup as BAND-IQ 009–011:

    python -m bridge.band_iq_front_porch \
      --workspace /private/vidmage-projects/your-song \
      --blender-root /private/donors/haunted-blender \
      --toaster-root /private/donors/haunted-toaster \
      --playdeck-root /private/donors/playdeck \
      --port 8767 --open-browser

In your own browser at **http://127.0.0.1:8767/**:

1. Bring a song and 2–12 photographs and approve their private use.
2. Prepare a real, song-timed Blender/Toaster paper plan.
3. Use the 010 Storytable to choose which source image belongs in each shot.
4. While that table is still **unsealed**, open the 012 THIS/THAT contact comparison for any particular shot. Select an alternate owned image, move the focal dials or protect text, then compare six real frames.
5. Explicitly **Apply THAT** if desired, or leave the original browser draft intact. Repeat on another shot without overwriting a previous sealed artifact.
6. When satisfied, sign the entire human-authored 010 Storytable. All 012 session previews are invalidated on that crossing.
7. Optionally develop the separate, create-only 011 Living Filmstrip **from the sealed story**.
8. Separately authorize the real first VidMage A and native Playdeck B movies, and enter the 008 Workbench. Existence of contact previews never counts as film-making consent.

Original uploaded song/photos, paper planning, 010 story receipts, 011 filmstrip, native A/B movies and the independent 004/007 human reviews all maintain their existing source and authority boundaries.

## Exact implementation

- \`bridge/band_iq_contact_sheet.py\`: bounded, no-write pure candidate validation and real six-frame VidMage raster sampling from the already verified native plan, images and Toaster audio observation. Explicit \`allowStorySeal:false\`, \`allowMovieRender:false\`, provider/network/publication flags false. SHA-256 digest over the complete source-attributed contact, no disk output.
- \`bridge/band_iq_front_porch.py\`: real owner-local \`compare_candidates()\` and \`contact_frame()\` inside the original session lock, fixed JPEG routes, same-origin/capability POST. Sealing a story invalidates the preview; final films remain separate. No new filesystem paths in HTTP request bodies.
- \`ui/band_iq_front_porch.{html,css,js}\`: analogue contact sheet, separately editable THAT dials, two three-frame strips, real time seeking, explicit apply/leave controls, stale-draft protection and accessible result status. No external JS/CSS dependencies; comparison pixels arrive only from the local server and aren't part of downloadable publication.
- \`tests/test_band_iq_contact_sheet.py\`: genuine decoded textured sources, two real competing choices, exact raster frame/timestamps/JPEG identities, same-image different focus, missing owned photo/shot refusal, changed source bytes, same-session determinism, rehashed photo spoof refusal, no movie or JSON artifacts.
- Updated \`tests/test_band_iq_front_porch.PorchNativeTests\`: actual short synthetic song and two owned photos → native Toaster/Blender prep → **012 local HTTP contact preview** with verified six JPEGs and cross-origin refusal → **010 actual story seal** invalidating stale session frames → **011 create-only filmstrip** → real VidMage A/native Playdeck B MP4s → independent human 004 choice → project restart. No artist media committed to GitHub.
- \`.github/workflows/band-iq-012.yml\`: distinct fast actual-pixel source checks and full native SHA-pinned Blender/Toaster/Playdeck audio/video end-to-end checks.

## Laws

CONTACT != STORY.

APPLY != SEAL.

A SCRATCH POSSIBILITY != A SOURCE RECEIPT.

PIXEL DIFFERENCE != AN AESTHETIC RANKING.

SEEKING A FRAME != RENDERING A MOVIE.

AN AUTHOR'S DRAFT != A MACHINE'S PROVISIONAL PROPOSAL.

PHOTO OWNERSHIP != PUBLICATION PERMISSION.

A TIME WINDOW != THE WHOLE PERFORMANCE.

## A possible 013 seam

A reversible, local **candidate tray** that can compare multiple *unsealed* storyboard possibilities for more than one shot, and copy a chosen coherent candidate back into the on-screen draft only after an artist acts. It must remain distinct from both the sealed 010 Storytable and the real 011 filmstrip. Not included in this PR.
