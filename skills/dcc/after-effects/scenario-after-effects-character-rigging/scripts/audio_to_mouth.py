#!/usr/bin/env python3
"""Turn a voice file into hold keys for N mouth shapes (0 = closed ... N-1 = widest), one RMS value per video frame.

Needs ffmpeg on PATH. Standard library only.
    python3 audio_to_mouth.py voice.wav --fps 24 --shapes 3 --min-hold 2 --lead 1 > mouth.json
Output: {"fps", "frames", "keys": [[frame, shape], ...], "thresholds_db", "counts"} ready for AEX.rig.holdKeys via --args.
Amplitude gives open versus closed, not phonemes: B, M, P and F, V need a person or a phoneme aligner.
"""
import argparse
import json
import re
import subprocess
import sys

FFMPEG_TIMEOUT_S = 600


def rms_per_frame(path, fps, rate=48000):
    n = int(round(rate / fps))
    if abs(rate / fps - n) > 1e-6:
        sys.exit("sample rate %d is not a multiple of %s fps: pick a rate that is" % (rate, fps))
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(rate), "-af",
           "asetnsamples=n=%d:p=0,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-" % n,
           "-f", "null", "-"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=FFMPEG_TIMEOUT_S).stdout
    except FileNotFoundError:
        sys.exit("ffmpeg not found on PATH: install it, then run again")
    except subprocess.TimeoutExpired:
        sys.exit("ffmpeg did not finish decoding %s within %d s" % (path, FFMPEG_TIMEOUT_S))
    except subprocess.CalledProcessError as e:
        sys.exit("ffmpeg failed on %s (exit %d): %s" % (path, e.returncode, (e.stderr or "").strip()))
    vals = []
    for m in re.finditer(r"RMS_level=(-?[\d.]+|-inf)", out):
        v = m.group(1)
        vals.append(-120.0 if v == "-inf" else float(v))
    return vals


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    i = min(len(sorted_vals) - 1, max(0, int(round(p / 100.0 * (len(sorted_vals) - 1)))))
    return sorted_vals[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--shapes", type=int, default=3)
    ap.add_argument("--silence", type=float, default=-45.0, help="dB under which the mouth is closed")
    ap.add_argument("--min-hold", type=int, default=2, help="frames a shape stays before it may change")
    ap.add_argument("--lead", type=int, default=1, help="frames the mouth moves before the sound")
    a = ap.parse_args()
    if a.shapes < 1:
        ap.error("--shapes must be 1 or more")
    if a.fps <= 0:
        ap.error("--fps must be above 0")
    db = rms_per_frame(a.audio, a.fps)
    if not db:
        sys.exit("no audio frames decoded from %s: ffmpeg returned no RMS level" % a.audio)
    voiced = sorted(v for v in db if v > a.silence)
    # thresholds between open shapes: evenly spaced percentiles of the voiced frames
    th = [pct(voiced, 100.0 * k / (a.shapes - 1)) for k in range(1, a.shapes - 1)] if a.shapes > 2 else []
    raw = []
    for v in db:
        if v <= a.silence:
            raw.append(0)
        else:
            s = 1
            for t in th:
                if v > t:
                    s += 1
            raw.append(min(s, a.shapes - 1))
    keys, cur, held = [], None, 0
    for f, s in enumerate(raw):
        if cur is None or (s != cur and held >= a.min_hold):
            cur, held = s, 0
            keys.append([max(0, f - a.lead), s])
        held += 1
    # the 1-frame lead shift can pull two keys closer than min-hold (first frames): the later sound wins, then merge repeats
    clean = []
    for k in keys:
        if clean and k[0] - clean[-1][0] < a.min_hold:
            clean[-1] = [clean[-1][0], k[1]]
        else:
            clean.append(k)
        if len(clean) > 1 and clean[-1][1] == clean[-2][1]:
            clean.pop()
    if clean and clean[-1][1] != 0:
        clean.append([len(db), 0])
    counts = {}
    for s in raw:
        counts[str(s)] = counts.get(str(s), 0) + 1
    json.dump({"fps": a.fps, "frames": len(db), "keys": clean, "thresholds_db": [round(t, 2) for t in th],
               "silence_db": a.silence, "counts": counts}, sys.stdout)


if __name__ == "__main__":
    main()
