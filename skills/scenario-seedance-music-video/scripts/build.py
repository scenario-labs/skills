#!/usr/bin/env python3
"""Cut a music video against its master audio, then verify the result.

Reads a small edit file, conforms every clip onto one timeline, concatenates,
muxes the untouched master, and checks the delivery. One ffmpeg pass.

    python3 scripts/build.py edit.json out.mp4

The master is never re-encoded when its codec can live in MP4 as is, so the
delivered soundtrack is bit for bit the file you supplied.
"""
# MIT. Ported from https://github.com/edemaistre/scenario-seedance-2-5-music-video,
# Copyright (c) 2026 Emmanuel de Maistre.

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

# Codecs that MP4 accepts without a re-encode.
COPYABLE = {"aac": "adts", "mp3": "mp3"}


class BuildError(RuntimeError):
    """Anything that should stop the build with a readable message."""


def run(args: list[str]) -> bytes:
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", "replace").strip()[-1200:]
        raise BuildError(f"{args[0]} failed\n{tail}")
    return proc.stdout


def probe(path: Path) -> dict:
    raw = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    return json.loads(raw)


def streams(info: dict, kind: str) -> list[dict]:
    return [s for s in info.get("streams", []) if s.get("codec_type") == kind]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def audio_fingerprint(path: Path, codec: str) -> str | None:
    """SHA-256 of the audio frames alone, so we can prove the master was copied, not re-encoded.

    Metadata is stripped on the way out. Without that, the mp3 muxer writes an ID3v2 header
    carrying whatever container tags it found, so the same frames hash differently depending
    on whether they came from a bare .mp3 or from inside an .mp4.
    """
    container = COPYABLE.get(codec)
    if container is None:
        return None
    data = run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-c", "copy",
         "-map_metadata", "-1", "-id3v2_version", "0", "-write_xing", "0", "-f", container, "-"]
    )
    return hashlib.sha256(data).hexdigest()


def video_frames(info: dict) -> int:
    video = streams(info, "video")
    if not video:
        raise BuildError("no video stream")
    counted = video[0].get("nb_frames")
    if counted and str(counted).isdigit() and int(counted) > 0:
        return int(counted)
    duration = float(info["format"]["duration"])
    num, den = (int(x) for x in video[0]["r_frame_rate"].split("/"))
    return int(round(duration * num / den))


def frames_at_fps(info: dict, fps: int) -> int:
    """Frame budget of a clip once the graph resamples it to the edit's fps.

    The filter graph applies fps=<target> before the frame trim, so a clip's
    native frame count is its budget only when the rates already agree;
    otherwise the count converts through the native rate (floor, so a clip
    is never credited a frame the resampler will not deliver).
    """
    native = video_frames(info)
    num, den = (int(x) for x in streams(info, "video")[0]["r_frame_rate"].split("/"))
    if num <= 0 or den <= 0 or num == fps * den:
        return native
    return native * den * fps // num


def load_edit(path: Path) -> dict:
    edit = json.loads(path.read_text())
    for key in ("master", "shots"):
        if key not in edit:
            raise BuildError(f"edit file is missing '{key}'")
    if not isinstance(edit["shots"], list) or not edit["shots"]:
        raise BuildError("edit file needs at least one shot")
    return edit


def plan(edit: dict, root: Path) -> dict:
    """Turn 'at' times into exact frame spans and check every clip is long enough."""
    fps = int(edit.get("fps", 24))
    width = int(edit.get("width", 1280))
    height = int(edit.get("height", 720))
    if fps <= 0 or width <= 0 or height <= 0:
        raise BuildError("fps, width and height must be positive")

    master = (root / edit["master"]).resolve()
    if not master.is_file():
        raise BuildError(f"master not found: {master}")
    master_info = probe(master)
    if not streams(master_info, "audio"):
        raise BuildError("master has no audio stream")
    master_duration = float(master_info["format"]["duration"])

    shots = edit["shots"]
    starts = [float(shot.get("at", 0.0)) for shot in shots]
    if starts[0] != 0.0:
        raise BuildError("the first shot must start at 0")
    for earlier, later in zip(starts, starts[1:]):
        if later <= earlier:
            raise BuildError("shot 'at' times must increase, and no two shots may share one")
    if starts[-1] >= master_duration:
        raise BuildError("the last shot starts at or after the end of the master")

    # Visuals must cover the whole master, so round the final boundary up.
    total_frames = math.ceil(master_duration * fps - 1e-9)
    bounds = [int(round(start * fps)) for start in starts] + [total_frames]

    planned = []
    for index, shot in enumerate(shots):
        span = bounds[index + 1] - bounds[index]
        if span <= 0:
            raise BuildError(f"shot {index} ('{shot.get('clip')}') has no frames")
        clip = (root / shot["clip"]).resolve()
        if not clip.is_file():
            raise BuildError(f"clip not found: {clip}")
        head = int(round(float(shot.get("in", 0.0)) * fps))
        if head < 0:
            raise BuildError(f"shot {index} has a negative 'in'")
        available = frames_at_fps(probe(clip), fps) - head
        if available < span:
            raise BuildError(
                f"{clip.name} gives {available} frames after the head trim but the edit needs {span}. "
                f"Generate it longer, or move the following shot later."
            )
        planned.append({"clip": clip, "head": head, "span": span, "start_frame": bounds[index]})

    return {
        "fps": fps,
        "width": width,
        "height": height,
        "master": master,
        "master_info": master_info,
        "master_duration": master_duration,
        "total_frames": total_frames,
        "shots": planned,
    }


def filter_graph(job: dict) -> str:
    fps, width, height = job["fps"], job["width"], job["height"]
    parts, labels = [], []
    for index, shot in enumerate(job["shots"]):
        label = f"v{index}"
        labels.append(f"[{label}]")
        parts.append(
            f"[{index}:v]fps={fps},"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:-1:-1:color=black,setsar=1,"
            f"trim=start_frame={shot['head']}:end_frame={shot['head'] + shot['span']},"
            f"setpts=PTS-STARTPTS,format=yuv420p[{label}]"
        )
    parts.append(f"{''.join(labels)}concat=n={len(labels)}:v=1:a=0[vcat]")
    parts.append(f"[vcat]trim=end_frame={job['total_frames']},setpts=PTS-STARTPTS[vout]")
    return ";".join(parts)


def render(job: dict, output: Path, crf: int) -> str:
    master_codec = streams(job["master_info"], "audio")[0]["codec_name"]
    copyable = master_codec in COPYABLE
    audio_index = len(job["shots"])

    command = ["ffmpeg", "-y", "-v", "error"]
    for shot in job["shots"]:
        command += ["-i", str(shot["clip"])]
    command += ["-i", str(job["master"])]
    command += [
        "-filter_complex", filter_graph(job),
        "-map", "[vout]",
        "-map", f"{audio_index}:a:0",
        # No -frames:v here. It ends the whole output once the video hits the limit, which
        # truncates the master whenever the audio runs past the last video frame. The trim
        # filter in the graph already fixes the count exactly.
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-r", str(job["fps"]),
    ]
    command += ["-c:a", "copy"] if copyable else ["-c:a", "aac", "-b:a", "320k"]
    command += ["-movflags", "+faststart", str(output)]

    output.parent.mkdir(parents=True, exist_ok=True)
    run(command)
    return "copy" if copyable else "aac_320k"


def verify(job: dict, output: Path, audio_mode: str, master_sha_before: str) -> dict:
    info = probe(output)
    video = streams(info, "video")
    audio = streams(info, "audio")
    checks: dict[str, bool] = {}

    checks["one_video_stream"] = len(video) == 1
    checks["one_audio_stream"] = len(audio) == 1
    if not (checks["one_video_stream"] and checks["one_audio_stream"]):
        return {"passed": False, "checks": checks, "detail": {}}

    frames = video_frames(info)
    checks["frame_count_exact"] = frames == job["total_frames"]
    checks["geometry"] = (video[0]["width"], video[0]["height"]) == (job["width"], job["height"])
    checks["frame_rate"] = video[0]["r_frame_rate"] == f"{job['fps']}/1"

    master_audio = streams(job["master_info"], "audio")[0]
    checks["audio_channels"] = int(audio[0]["channels"]) == int(master_audio["channels"])
    checks["audio_starts_at_zero"] = abs(float(audio[0].get("start_time", 0.0))) < 1e-6

    master_codec = master_audio["codec_name"]
    if audio_mode == "copy":
        before = audio_fingerprint(job["master"], master_codec)
        after = audio_fingerprint(output, audio[0]["codec_name"])
        checks["audio_bit_exact"] = before is not None and before == after
    else:
        # MP4 cannot carry this codec, so one documented AAC encode is the honest best case.
        # There is nothing to compare bit for bit, but it must still be a single pass.
        checks["audio_encoded_once"] = audio[0]["codec_name"] == "aac"

    master_duration = job["master_duration"]
    final_audio_duration = float(audio[0].get("duration", master_duration))
    checks["audio_duration_preserved"] = abs(final_audio_duration - master_duration) <= 1.0 / job["fps"]

    checks["master_untouched"] = sha256_file(job["master"]) == master_sha_before

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "detail": {
            "frames": frames,
            "expected_frames": job["total_frames"],
            "size": f"{video[0]['width']}x{video[0]['height']}",
            "fps": video[0]["r_frame_rate"],
            "video_codec": video[0]["codec_name"],
            "audio_codec": audio[0]["codec_name"],
            "audio_mode": audio_mode,
            "master_duration_seconds": round(master_duration, 6),
            "output_duration_seconds": round(float(info["format"]["duration"]), 6),
        },
    }


def build(edit_path: Path, output: Path, root: Path | None = None, crf: int = 18) -> dict:
    edit_path = Path(edit_path)
    root = Path(root) if root else edit_path.parent
    job = plan(load_edit(edit_path), root)
    master_sha = sha256_file(job["master"])
    audio_mode = render(job, Path(output), crf)
    report = verify(job, Path(output), audio_mode, master_sha)
    report["output"] = str(output)
    report["master_sha256"] = master_sha
    report["shots"] = [
        {
            "clip": shot["clip"].name,
            "timeline_start_frame": shot["start_frame"],
            "frames": shot["span"],
            "head_trim_frames": shot["head"],
        }
        for shot in job["shots"]
    ]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cut a music video against its master audio.")
    parser.add_argument("edit", type=Path, help="edit file, format shown in SKILL.md")
    parser.add_argument("output", type=Path, help="delivery MP4 to write")
    parser.add_argument("--root", type=Path, default=None, help="base for relative paths, defaults to the edit file's folder")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality, lower is better (default 18)")
    args = parser.parse_args(argv)

    try:
        report = build(args.edit, args.output, args.root, args.crf)
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    if not report["passed"]:
        failed = [name for name, ok in report["checks"].items() if not ok]
        print(f"\nFAILED: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(f"\nOK  {report['detail']['frames']} frames, audio {report['detail']['audio_mode']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
