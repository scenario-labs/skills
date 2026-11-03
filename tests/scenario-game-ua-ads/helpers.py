"""Load the shipped scripts by path and build tiny inputs: PNGs, WAVs, clips.

The scripts import each other by bare name (`import build_passes`), so the scripts directory goes
on sys.path and each loaded module is registered under its bare name.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SCRIPTS = Path(__file__).resolve().parents[2] / "skills/scenario-game-ua-ads/scripts"
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
SR = 48000

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(script, *args, cwd=None):
    """Run a shipped script as the agent would."""
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], cwd=cwd,
                          capture_output=True, text=True)


def rect_png(path, size, box, color=(255, 255, 255, 255)):
    """A transparent PNG with one opaque rectangle covering box (x0, y0, x1, y1), x1 and y1 exclusive."""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([box[0], box[1], box[2] - 1, box[3] - 1], fill=color)
    im.save(path)
    return path


def write_json(path, data):
    Path(path).write_text(json.dumps(data))
    return path


def write_wav(path, x):
    """16-bit stereo WAV at 48 kHz from a mono or stereo float array."""
    x = np.asarray(x, np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).round().astype("<i2").tobytes())
    return path


def tone(seconds, amp=0.1, freq=440.0):
    t = np.arange(round(seconds * SR)) / SR
    return amp * np.sin(2 * np.pi * freq * t)


def burst(seconds=0.12, amp=0.5, seed=0):
    """A decaying noise hit whose sound starts at sample 0, normalized to peak at amp."""
    x = np.random.default_rng(seed).standard_normal(round(seconds * SR)) * np.exp(-np.arange(round(seconds * SR)) / (0.02 * SR))
    return amp * x / np.abs(x).max()


def video_stream(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=codec_name,pix_fmt,width,height,nb_read_frames", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["streams"][0]


def mux(path, audio, size=(64, 112), seconds=2):
    """A black clip at 30 fps carrying audio as PCM, a stand-in for a composed master."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s={size[0]}x{size[1]}:r=30:d={seconds}",
                    "-i", str(audio), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-shortest",
                    str(path)], check=True)
    return path
