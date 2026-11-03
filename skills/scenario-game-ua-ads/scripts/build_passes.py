#!/usr/bin/env python3
"""Write the compose payloads of an ad's picture and sound passes, and sum its sound locally.

Usage:
  python3 build_passes.py picture plan.json [-o payload_picture.json]
  python3 build_passes.py simulate plan.json [-o sim.wav]
  python3 build_passes.py sound plan.json SILENT_MASTER_ASSET_ID [-o payload_sound.json]

picture: the picture-pass payload for model_scenario-compose-video. Every video layer is muted,
  no audio layer goes in, compressionLevel is 15. Composed, it gives the silent master.
simulate: sums the sound pass from the local files exactly as the payload lays it out, with no
  limiter, as compose has none. Prints integrated LUFS and true peak (ebur128), the 50 ms
  windows over -1 dBFS with the hits sounding there, and each hit's peak margin over the music
  and beds in a 50 ms window around its peak. Run it before the sound pass and trim until the
  true peak is at or under -1 dBTP while every hit keeps 4 dB.
sound: the sound-pass payload (the silent master as the one video layer, then every audio layer)
  and cues.json beside it, for check_master.py.

plan.json (paths relative to it; picture times are frame numbers, sound times seconds or "frame"):
{
  "fps": 30, "canvas": [1080, 1920], "duration": 15.0, "sections": [0, 5.2, 11.1],
  "assets": {"fail.mp4": "<asset id>", "hand_fail.mov": "<asset id>", "tap.wav": "<asset id>"},
  "tracks": "tracks/layers.json",
  "picture": [
    {"file": "fail.mp4", "type": "video", "start": 0, "end": 156, "trimEnd": 2.8},
    {"track": "hand_fail"},
    {"file": "overlays/fail.png", "type": "image", "x": 244, "y": 400, "start": 72, "end": 108,
     "transitionIn": "zoomin", "transitionDuration": 0.2},
    {"still": "icon_pop"}
  ],
  "sound": {
    "master_db": -4,
    "music": [{"file": "music.mp3", "offset": 2.0, "end": 12.9,
               "gains": [[0, -4], [2.25, -8], [3.6, -10]]}],
    "beds": [{"file": "bed.mp3", "t": 3.7, "gain_db": -2}],
    "hits": [{"label": "tap", "file": "tap.wav", "frame": 13, "gain_db": -2, "trim_db": -1}]
  }
}
- assets maps each uploaded file (its name or its path in the plan) to its asset id. A layer may
  give "source" directly instead of "file".
- picture: list order is the stacking order unless a layer sets zIndex. "track" and "still" take
  the layer render_tracks.py wrote ("group/child" for a still inside a group). Other compose keys
  pass through. A video defaults to the full canvas with fit "cover"; an image gets its natural
  width and height from the file, since compose draws an unsized image at the wrong scale.
- music: one read of the file, file time = ad time + offset. "gains" steps the gain in dB at
  each time, so every duck splits it into segments with their own trimStart and 10 ms fades at
  each split; fade_in_s and fade_out_s set the outer fades. end defaults to the file's end.
- beds: video-to-audio tracks, "t" or "frame", gain_db, optional trimStart and end. Past 49
  audio layers they are dropped first.
- hits: "frame" or "t", gain_db, trim_db (a per-hit trim against peaks), trimStart (seconds into
  the file), dur_s. Every hit file starts its sound at 0, so its time is the event's time.
- master_db trims every audio layer. Volumes are linear (10^(dB/20), 3 decimals, at most 2).
"""

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SR = 48000
MAX_LAYERS = 50
MAX_AUDIO = MAX_LAYERS - 1
PICTURE_KEYS = ("file", "start", "end", "track", "still")


class PlanError(Exception):
    pass


def floor_ms(t):
    return math.floor(t * 1000 + 1e-6) / 1000


def frame_ms(n, fps):
    """Compose time of a frame. Rounded up (185 / 30 as 6.167), a layer starts one frame late."""
    return n * 1000 // fps / 1000


def db(x):
    return 20 * math.log10(x) if x > 1e-9 else float("-inf")


def volume(gain_db):
    return min(2.0, round(10 ** (gain_db / 20), 3))


_audio = {}


def load_audio(path):
    """Stereo float32 at 48 kHz."""
    path = str(path)
    if path not in _audio:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        _audio[path] = np.frombuffer(raw, np.float32).reshape(-1, 2)
    return _audio[path]


def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", str(path)], input=np.ascontiguousarray(x, np.float32).tobytes(), check=True)


def loudness(path):
    """Integrated LUFS and true peak (dBTP) from ffmpeg's ebur128 summary."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    if "Summary:" not in err:
        raise PlanError(f"ebur128 gave no summary for {path}")
    s = err.rsplit("Summary:", 1)[1]
    number = r"([-+]?(?:\d+(?:\.\d+)?|inf))"
    return (float(re.search(r"I:\s*" + number + r"\s*LUFS", s).group(1)),
            float(re.search(r"Peak:\s*" + number + r"\s*dBFS", s).group(1)))


class Plan:
    def __init__(self, path):
        self.path = Path(path)
        self.base = self.path.parent
        self.raw = json.loads(self.path.read_text())
        self.fps = self.raw.get("fps", 30)
        self.canvas = tuple(self.raw.get("canvas", (1080, 1920)))
        self.duration = float(self.raw["duration"])
        self.assets = self.raw.get("assets", {})

    def file(self, name):
        return self.base / name

    def asset(self, name):
        for key in (name, Path(name).name):
            if key in self.assets:
                return self.assets[key]
        raise PlanError(f"no asset id for {name}: upload it and add it to \"assets\"")

    def time(self, item, key="t"):
        if "frame" in item:
            return frame_ms(item["frame"], self.fps)
        return floor_ms(item[key])

    def settings(self, compression):
        return {"canvasMode": "custom", "canvasWidth": self.canvas[0], "canvasHeight": self.canvas[1],
                "durationMode": "custom", "duration": self.duration, "fps": self.fps,
                "compressionLevel": compression, "backgroundColor": "#000000"}


def picture_payload(plan):
    tracks = {}
    if "tracks" in plan.raw:
        tracks = json.loads(plan.file(plan.raw["tracks"]).read_text())["layers"]
    layers, notes = [], []
    for i, e in enumerate(plan.raw["picture"]):
        extra = {k: v for k, v in e.items() if k not in PICTURE_KEYS}
        if "track" in e:
            entry = tracks.get(e["track"]) or {}
            if "layer" not in entry:
                raise PlanError(f"no track {e['track']!r} in {plan.raw.get('tracks')}")
            lay = {**entry["layer"], "source": plan.asset(entry["file"])}
        elif "still" in e:
            group, _, child = e["still"].partition("/")
            entry = tracks.get(group, {})
            entry = entry.get("parts", {}).get(child, {}) if child else entry
            if "still" not in entry:
                raise PlanError(f"no still for {e['still']!r}: give its icon_pop an \"until\" frame")
            lay = {**entry["still"], "source": plan.asset(entry["still"]["source"])}
        else:
            if "start" not in e or "end" not in e:
                raise PlanError(f"picture layer {i} needs start and end frames")
            lay = {"source": e.get("source") or plan.asset(e["file"]),
                   "startTime": frame_ms(e["start"], plan.fps), "endTime": frame_ms(e["end"], plan.fps)}
            if extra.get("type") == "video":
                lay.update({"x": "0", "y": "0", "width": str(plan.canvas[0]), "height": str(plan.canvas[1]), "fit": "cover"})
            elif extra.get("type") == "image":
                if "width" not in extra and "file" not in e:
                    raise PlanError(f"image layer {i} needs its file or an explicit width and height")
                if "file" in e:
                    with Image.open(plan.file(e["file"])) as im:
                        lay.update({"width": im.width, "height": im.height})
                lay["fit"] = "fill"
        lay.update(extra)
        if lay.get("type") == "audio":
            raise PlanError("the picture pass takes no audio layer: put sounds in the sound pass")
        if lay.get("type") == "video":
            lay["mute"] = True
        for k in ("x", "y", "width", "height"):
            if k in lay:
                lay[k] = str(lay[k])
        lay.setdefault("zIndex", i)
        if lay.get("type") == "image" and min(int(lay["width"]), int(lay["height"])) < 300:
            notes.append(f"layer {i} ({lay['source']}): an image under 300 px on a side; pad it to about 300 px")
        if lay["endTime"] > plan.duration:
            notes.append(f"layer {i} ({lay['source']}): ends at {lay['endTime']} s, past the {plan.duration} s ad")
        layers.append(lay)
    if len(layers) > MAX_LAYERS:
        raise PlanError(f"{len(layers)} layers: compose takes {MAX_LAYERS}. Merge tracks into a group.")
    return {"layers": layers, **plan.settings(15)}, notes


def sound_rows(plan, with_ids=True):
    """Every audio layer of the sound pass as (role, label, file, layer), and the notes."""
    snd, notes, rows = plan.raw["sound"], [], []
    master, end_all = snd.get("master_db", 0.0), plan.duration

    def source(f):
        return plan.asset(f) if with_ids else Path(f).name

    def length(f, trim=0.0):
        return len(load_audio(plan.file(f))) / SR - trim

    for m in snd.get("music", []):
        offset, gains = m.get("offset", 0.0), sorted(m["gains"])
        end = min(end_all, m.get("end", length(m["file"]) - offset))
        cuts = [(t, g) for t, g in gains if t < end]
        for k, (t0, gain) in enumerate(cuts):
            t1 = cuts[k + 1][0] if k + 1 < len(cuts) else end
            if t0 + offset < 0:
                raise PlanError(f"music {m['file']}: offset {offset} reads before the file starts at {t0} s")
            lay = {"source": source(m["file"]), "type": "audio", "startTime": floor_ms(t0), "endTime": floor_ms(t1),
                   "volume": volume(gain + master)}
            if t0 + offset > 0:
                lay["trimStart"] = floor_ms(t0 + offset)
            lay["audioFadeIn"] = m.get("fade_in_s", 0.01) if k == 0 else 0.01
            lay["audioFadeOut"] = m.get("fade_out_s", 0.01) if k == len(cuts) - 1 else 0.01
            rows.append(("music", m.get("label", f"music {Path(m['file']).name} {t0:g}s"), m["file"], lay))
    for b in snd.get("beds", []):
        t0, trim = plan.time(b), b.get("trimStart", 0.0)
        t1 = min(end_all, floor_ms(b["end"]) if "end" in b else floor_ms(t0 + length(b["file"], trim)))
        lay = {"source": source(b["file"]), "type": "audio", "startTime": t0, "endTime": t1,
               "volume": volume(b.get("gain_db", 0.0) + master)}
        if trim:
            lay["trimStart"] = floor_ms(trim)
        for key, name in (("fade_in_s", "audioFadeIn"), ("fade_out_s", "audioFadeOut")):
            if key in b:
                lay[name] = b[key]
        rows.append(("bed", b.get("label", f"bed {Path(b['file']).name}"), b["file"], lay))
    for h in snd.get("hits", []):
        t0, trim = plan.time(h), h.get("trimStart", 0.0)
        t1 = min(end_all, floor_ms(t0 + h.get("dur_s", length(h["file"], trim))))
        gain = h.get("gain_db", 0.0) + h.get("trim_db", 0.0) + master
        lay = {"source": source(h["file"]), "type": "audio", "startTime": t0, "endTime": t1, "volume": volume(gain)}
        if trim:
            lay["trimStart"] = floor_ms(trim)
        if 10 ** (gain / 20) > 2:
            notes.append(f"{h.get('label', h['file'])}: {gain:+.1f} dB is over the volume cap of 2, clamped")
        rows.append(("hit", h.get("label", Path(h["file"]).stem), h["file"], lay))
    if len(rows) > MAX_AUDIO:
        beds = [r for r in rows if r[0] == "bed"]
        rows = [r for r in rows if r[0] != "bed"]
        notes += [f"dropped {label}: past {MAX_AUDIO} audio layers the bed goes first" for _, label, _, _ in beds]
    if len(rows) > MAX_AUDIO:
        raise PlanError(f"{len(rows)} audio layers without the beds: compose takes {MAX_AUDIO} beside the silent "
                        "master. Cut or merge hits.")
    return rows, notes


def render_layer(plan, file, lay, total):
    """One audio layer placed on the timeline as compose lays it out: trim, volume, linear fades."""
    x = load_audio(plan.file(file))
    s0 = round(lay.get("trimStart", 0) * SR)
    y = x[s0:s0 + round((lay["endTime"] - lay["startTime"]) * SR)] * np.float32(lay["volume"])
    fade_in = min(len(y), round(lay.get("audioFadeIn", 0) * SR))
    fade_out = min(len(y), round(lay.get("audioFadeOut", 0) * SR))
    if fade_in:
        y[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]
    if fade_out:
        y[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)[:, None]
    out = np.zeros((total, 2), np.float32)
    p = round(lay["startTime"] * SR)
    if p < total:
        n = min(len(y), total - p)
        out[p:p + n] = y[:n]
    return out


def hit_margin(hit, music, start, search=0.3, half=0.025):
    """dB of the hit's peak over the music's peak in the 50 ms around it, and when that peak sounds."""
    seg = np.abs(hit[start:start + round(search * SR)]).max(axis=1) if start < len(hit) else np.zeros(0)
    if not seg.size or seg.max() <= 0:
        return None, None
    k = start + int(seg.argmax())
    w = round(half * SR)
    return db(float(seg.max())) - db(float(np.abs(music[max(0, k - w):k + w]).max())), (k - start) / SR


def onset_ms(plan, file, trim=0.0, rel_db=-30):
    x = np.abs(load_audio(plan.file(file))[round(trim * SR):]).max(axis=1)
    if not x.size or x.max() <= 0:
        return None
    return 1000 * int(np.argmax(x > x.max() * 10 ** (rel_db / 20))) / SR


def simulate(plan, out):
    rows, notes = sound_rows(plan, with_ids=False)
    total = round(plan.duration * SR)
    full, music, hits = np.zeros((total, 2), np.float32), np.zeros((total, 2), np.float32), []
    for role, label, file, lay in rows:
        y = render_layer(plan, file, lay, total)
        full += y
        if role == "hit":
            hits.append((label, file, lay, y))
        else:
            music += y
    write_wav(out, full)
    lufs, tp = loudness(out)
    peak = db(float(np.abs(full).max()))
    print(f"simulated sound pass, {len(rows)} audio layers: {lufs:.1f} LUFS, true peak {tp:+.1f} dBTP, "
          f"sample peak {peak:+.1f} dBFS (no limiter) -> {out}")
    if tp > -1:
        print("  true peak over -1 dBTP: lower master_db, or trim_db on the hits sounding in the windows below")
    if not -16 <= lufs <= -14:
        print("  outside -16 to -14 LUFS: adjust master_db, or plan the loudness pass")
    win = SR // 20
    for k in range(0, total, win):
        if np.abs(full[k:k + win]).max() > 10 ** (-1 / 20):
            active = [label for label, _, lay, _ in hits if lay["startTime"] <= (k + win) / SR and lay["endTime"] > k / SR]
            print(f"  over -1 dBFS at {k / SR:6.2f} s: {', '.join(active) or 'music and beds only'}")
    report = {"lufs": lufs, "true_peak": tp, "sample_peak": peak, "hits": []}
    for label, file, lay, y in hits:
        margin, at = hit_margin(y, music, round(lay["startTime"] * SR))
        onset = onset_ms(plan, file, lay.get("trimStart", 0.0))
        flags = [f for f, bad in (("LOW", margin is not None and margin < 4),
                                  (f"onset +{onset:.0f} ms, trim the file to start at 0", onset is not None and onset > 10)) if bad]
        shown = "silent" if margin is None else ("no music" if math.isinf(margin) else f"{margin:+5.1f} dB")
        print(f"  {lay['startTime']:7.3f} s  {label:24s} vol {lay['volume']:5.3f}  over music {shown}  {' '.join(flags)}")
        report["hits"].append({"label": label, "t": lay["startTime"], "margin_db": margin, "peak_at": at, "onset_ms": onset})
    for n in notes:
        print(f"NOTE {n}", file=sys.stderr)
    return report


def sound_payload(plan, silent_id):
    rows, notes = sound_rows(plan)
    W, H = plan.canvas
    layers = [{"source": silent_id, "type": "video", "startTime": 0.0, "endTime": plan.duration, "x": "0", "y": "0",
               "width": str(W), "height": str(H), "fit": "cover", "mute": True, "zIndex": 0}]
    layers += [lay for _, _, _, lay in rows]
    cues = {"duration": plan.duration, "fps": plan.fps, "canvas": list(plan.canvas),
            "sections": plan.raw.get("sections", [0]),
            "cues": [{"label": label, "role": role, "file": str(plan.file(file).resolve()), "t": lay["startTime"],
                      "end": lay["endTime"], "trimStart": lay.get("trimStart", 0.0), "volume": lay["volume"]}
                     for role, label, file, lay in rows]}
    return {"layers": layers, **plan.settings(18)}, cues, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("picture", "simulate", "sound"):
        p = sub.add_parser(name)
        p.add_argument("plan", type=Path)
        if name == "sound":
            p.add_argument("silent_master", help="asset id of the composed picture pass")
        p.add_argument("-o", "--out", type=Path)
    args = ap.parse_args(argv)
    try:
        plan = Plan(args.plan)
        if args.cmd == "picture":
            payload, notes = picture_payload(plan)
            out = args.out or plan.base / "payload_picture.json"
            out.write_text(json.dumps(payload, indent=1) + "\n")
            print(f"picture pass: {len(payload['layers'])} layers -> {out}")
        elif args.cmd == "simulate":
            simulate(plan, args.out or plan.base / "sim.wav")
            notes = []
        else:
            payload, cues, notes = sound_payload(plan, args.silent_master)
            out = args.out or plan.base / "payload_sound.json"
            out.write_text(json.dumps(payload, indent=1) + "\n")
            (out.parent / "cues.json").write_text(json.dumps(cues, indent=1) + "\n")
            print(f"sound pass: {len(payload['layers']) - 1} audio layers -> {out}, cues -> {out.parent / 'cues.json'}")
    except (PlanError, KeyError) as e:
        print(f"error: {e if isinstance(e, PlanError) else f'missing key {e}'}", file=sys.stderr)
        return 2
    for n in notes:
        print(f"NOTE {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
