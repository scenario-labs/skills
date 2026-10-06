#!/usr/bin/env python3
"""Measure a song so a trailer can be cut to it: tempo, beat grid, loud sections, silences and strongest hits.

Usage: python3 song_hits.py <song.mp3|wav> <out.json> [--force]

Needs ffmpeg on the PATH and numpy. Prints a short summary and writes the full analysis as JSON.
"""
import json
import os
import subprocess
import sys

import numpy as np

SR, HOP, WIN = 22050, 256, 1024


def usage(code=1):
    print(__doc__.strip())
    sys.exit(code)


def load(path):
    try:
        raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
    except FileNotFoundError:
        sys.exit("ffmpeg is not on the PATH; install it first")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ffmpeg could not read {path}: {e.stderr.decode(errors='replace').strip()}")
    x = np.frombuffer(raw, np.float32)
    if len(x) < SR:
        sys.exit(f"{path}: under one second of audio")
    return x


def onset_strength(x):
    frames = [np.abs(np.fft.rfft(x[i:i + WIN] * np.hanning(WIN))) for i in range(0, len(x) - WIN, HOP)]
    spec = np.log1p(np.array(frames))
    flux = np.maximum(np.diff(spec, axis=0), 0).sum(1)
    return (flux - flux.mean()) / (flux.std() + 1e-9)


def tempo(flux):
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac)) * HOP / SR
    band = (lags > 0.33) & (lags < 1.0)  # 60 to 180 bpm
    period = float(lags[band][np.argmax(ac[band])])
    return period, 60.0 / period


def loudness(x, step=0.5):
    out = []
    for start in np.arange(0, len(x) / SR, step):
        seg = x[int(start * SR):int((start + step) * SR)]
        db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else -120.0
        out.append((round(float(start), 2), round(float(db), 1)))
    return out


def sections(levels, quiet=-35.0, loud=-16.0):
    """Group the loudness curve into silent, quiet, mid and loud runs."""
    def kind(db):
        return "silence" if db < quiet else "loud" if db > loud else "mid"
    runs = []
    for t, db in levels:
        k = kind(db)
        if runs and runs[-1]["kind"] == k:
            runs[-1]["end"] = t + 0.5
        else:
            runs.append({"kind": k, "start": t, "end": t + 0.5})
    return runs


def main():
    args = [a for a in sys.argv[1:] if a != "--force"]
    if len(args) != 2:
        usage()
    song, out = args
    if not os.path.exists(song):
        sys.exit(f"not found: {song}")
    if os.path.realpath(out) == os.path.realpath(song):
        sys.exit("the output path is the song itself; choose another file")
    if os.path.exists(out) and "--force" not in sys.argv:
        sys.exit(f"{out} exists; pass --force to overwrite")
    x = load(song)
    flux = onset_strength(x)
    period, bpm = tempo(flux)
    times = np.arange(len(flux)) * HOP / SR
    peaks = [i for i in range(1, len(flux) - 1) if flux[i] > 2.5 and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    onsets, last = [], -1.0
    for i in peaks:
        if times[i] - last > 0.2:
            onsets.append(round(float(times[i]), 2))
            last = times[i]
    strongest = sorted(sorted(peaks, key=lambda i: -flux[i])[:8])
    levels = loudness(x)
    report = {
        "duration": round(len(x) / SR, 2),
        "bpm": round(bpm, 1),
        "beat_seconds": round(period, 3),
        "bar_seconds": round(period * 4, 3),
        "onsets": onsets,
        "strongest_hits": [round(float(times[i]), 2) for i in strongest],
        "sections": sections(levels),
        "loudness_db_per_half_second": levels,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print(f"{report['duration']} s, {report['bpm']} bpm (beat {report['beat_seconds']} s, bar {report['bar_seconds']} s)")
    for s in report["sections"]:
        print(f"  {s['start']:6.1f} to {s['end']:6.1f} s  {s['kind']}")
    print("strongest hits:", ", ".join(f"{t} s" for t in report["strongest_hits"]))


if __name__ == "__main__":
    main()
