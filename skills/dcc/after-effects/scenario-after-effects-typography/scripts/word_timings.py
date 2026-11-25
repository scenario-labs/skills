#!/usr/bin/env python3
"""word_timings.py: speech-recognition word timestamps -> word timing JSON in frames for After Effects.

Input: a JSON transcript with word timestamps (segments[].words[] with word, start, end in seconds),
for example from a local speech-to-text run with word timestamps on. Optional: the stderr of an
ffmpeg silencedetect pass, used to cross-check phrase onsets and to split phrases.

Output (stdout or --out): {"fps", "lead", "words": [{"i", "word", "start", "end", "f0", "f1", "frames", "phrase"}],
"phrases": [{"p", "text", "f0", "f1"}], "checks": {...}}. Pass it to a job with --args.

Standard library only.
"""
import argparse
import json
import re
import sys


def load_words(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    words = []
    for seg in data.get("segments", []) if isinstance(data, dict) else []:
        for w in seg.get("words", []):
            text = w.get("word", "").strip()
            if text:
                words.append({"word": text, "start": float(w["start"]), "end": float(w["end"])})
    if not words and isinstance(data, list):  # already a flat list of {word,start,end}
        words = [{"word": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])} for w in data]
    return words


def load_silences(path):
    starts, ends = [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.search(r"silence_start: ([0-9.]+)", line)
            if m:
                starts.append(float(m.group(1)))
            m = re.search(r"silence_end: ([0-9.]+)", line)
            if m:
                ends.append(float(m.group(1)))
    return starts, ends


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--lead", type=int, default=1, help="frames the word appears BEFORE its spoken onset")
    ap.add_argument("--silence", help="ffmpeg silencedetect stderr log")
    ap.add_argument("--gap", type=float, default=0.18, help="seconds of pause that start a new phrase")
    ap.add_argument("--min-frames", type=int, default=6, help="flag words held for fewer frames than this")
    ap.add_argument("--out")
    a = ap.parse_args()

    words = load_words(a.transcript)
    if not words:
        sys.exit("no words with timestamps found in " + a.transcript)
    fps = a.fps
    phrase, out = 0, []
    for i, w in enumerate(words):
        if i > 0 and (w["start"] - words[i - 1]["end"] >= a.gap or re.search(r"[.!?]$", words[i - 1]["word"])):
            phrase += 1
        f0 = max(0, int(round(w["start"] * fps)) - a.lead)
        out.append({"i": i + 1, "word": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3),
                    "f0": f0, "f1": int(round(w["end"] * fps)), "phrase": phrase})
    # a word stays on screen until the next word of its phrase arrives, or its own end
    for i, w in enumerate(out):
        nxt = out[i + 1]["f0"] if i + 1 < len(out) else w["f1"]
        w["frames"] = max(1, nxt - w["f0"])
    phrases = []
    for w in out:
        if not phrases or phrases[-1]["p"] != w["phrase"]:
            phrases.append({"p": w["phrase"], "text": w["word"], "f0": w["f0"], "f1": w["f1"]})
        else:
            phrases[-1]["text"] += " " + w["word"]
            phrases[-1]["f1"] = w["f1"]
    checks = {"words": len(out), "phrases": len(phrases),
              "increasing": all(out[i]["f0"] <= out[i + 1]["f0"] for i in range(len(out) - 1)),
              "short": [w["word"] for w in out if w["frames"] < a.min_frames]}
    if a.silence:
        _, ends = load_silences(a.silence)
        offs = []
        for p in phrases[1:]:
            onset = out[[w["phrase"] for w in out].index(p["p"])]["start"]
            near = min(ends, key=lambda e: abs(e - onset)) if ends else None
            if near is not None:
                offs.append(round((onset - near) * fps, 2))
        checks["phrase_onset_vs_silence_end_frames"] = offs
        checks["silence_agrees"] = all(abs(o) <= 2 for o in offs)
    res = {"fps": fps, "lead": a.lead, "words": out, "phrases": phrases, "checks": checks}
    text = json.dumps(res, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text if not a.out else json.dumps(checks))


if __name__ == "__main__":
    main()
