"""Paula's consent-driven manual Kling clip intake and verified MP4 first cut.

Kling is an external service. Clip provenance is creator-reported; Vidmage can
verify *uploaded bytes*, not whether Kling generated them. No Kling API is called.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .engine import probe, run, sha_file

MAX_CLIP_BYTES = 75_000_000   # below Cloudflare free upload limits
MAX_CLIPS = 12
MAX_TOTAL_SECONDS = 90


def inspect_clip(path: Path) -> dict[str, Any]:
    info = probe(path)
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    try:
        duration = float(info.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        raise ValueError("This video has no usable duration") from None
    if not streams or not 1 <= duration <= 30:
        raise ValueError("Use an MP4 clip between 1 and 30 seconds")
    if path.stat().st_size > MAX_CLIP_BYTES:
        raise ValueError("Video exceeds the 75 MB upload limit")
    width = int(streams[0].get("width", 0))
    height = int(streams[0].get("height", 0))
    if not 64 <= width <= 8192 or not 64 <= height <= 8192:
        raise ValueError("Unsupported video dimensions")
    return {"duration_seconds": round(duration, 3),
            "width": width, "height": height, "sha256": sha_file(path),
            "bytes": path.stat().st_size, "media_kind": "creator-imported-mp4"}


def render_clip_cut(clips: list[Path], soundtrack: Path | None,
                    outdir: Path, *, width: int = 720, height: int = 1280) -> dict[str, Any]:
    """Join clips in upload order; optionally replace native audio with soundtrack.

    Does not call Kling or other paid services. Makes a completely new MP4 file.
    """
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg is required")
    if not 1 <= len(clips) <= MAX_CLIPS:
        raise ValueError("Add 1–12 clips before making the cut")
    if (width, height) not in {(720, 1280), (1280, 720)}:
        raise ValueError("Choose tall or wide orientation")
    inspections = [inspect_clip(path) for path in clips]
    total = sum(float(c["duration_seconds"]) for c in inspections)
    if total > MAX_TOTAL_SECONDS:
        raise ValueError("Clip total exceeds 90 seconds; choose fewer clips")
    outdir.mkdir(parents=True, exist_ok=True)
    destination = outdir / "movie.mp4"
    command = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y"]
    for path in clips:
        command += ["-i", str(path)]
    if soundtrack:
        command += ["-stream_loop", "-1", "-i", str(soundtrack)]
    filters: list[str] = []
    for i in range(len(clips)):
        filters.append(
            f"[{i}:v:0]fps=24,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,setpts=PTS-STARTPTS[v{i}]"
        )
    if len(clips) == 1:
        filters.append("[v0]null[v]")
    else:
        filters.append("".join(f"[v{i}]" for i in range(len(clips)))
                       + f"concat=n={len(clips)}:v=1:a=0[v]")
    command += ["-filter_complex", ";".join(filters), "-map", "[v]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-preset", "ultrafast", "-crf", "24",
                "-movflags", "+faststart"]
    if soundtrack:
        command += ["-map", f"{len(clips)}:a:0", "-c:a", "aac", "-b:a", "128k"]
    else:
        command.append("-an")
    command += ["-t", f"{total:.3f}", str(destination)]
    run(command, timeout=240)
    result = inspect_clip(destination)
    if abs(result["duration_seconds"] - total) > 1.5:
        raise RuntimeError("Clip-cut output duration does not match source timeline")
    return {"path": str(destination), "sha256": result["sha256"],
            "bytes": result["bytes"], "duration_seconds": result["duration_seconds"],
            "width": result["width"], "height": result["height"],
            "media_kind": "real-local-ffmpeg-mp4",
            "renderer": "paula-kling-clip-cut/v1",
            "clip_sha256": [c["sha256"] for c in inspections],
            "clip_count": len(clips),
            "native_clip_audio": "replaced-with-soundtrack" if soundtrack else "muted",
            "provider_provenance": "creator-reported; not API-verified",
            "external_ai_credits": 0}
