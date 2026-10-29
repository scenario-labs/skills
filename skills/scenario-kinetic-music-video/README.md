# scenario-kinetic-music-video (maintainer notes, not packaged)

## Origin

Sara Nemati own `kinetic-music-video` skill, built from the production of the Every Scenario music
video (and the kinetic music video it grew out of) and rewritten to be generic: any subject or none,
any looks, no project examples. Brought into this repository from the ZIP she exported on
2026-10-02.

## Edits for this repository

- Frontmatter reduced to `name`, `description` ("Use when", under 500 characters) and `license`; the
  name carries the `scenario-` prefix.
- Generative model names and ids removed (availability differs per team): lanes are named by
  capability and found with `recommend`. Parameter names are the ones that held at authoring time,
  with the schema as the authority.
- Credit amounts stated as relative costs, with `dry_run` before paid steps.
- En and em dashes replaced, scripts print usage when called without arguments, and the
  output-writing scripts refuse to replace an existing file without `--force`.
- Sibling references and the install invitation added; connection setup points to `scenario`.

## Portrait canvas

Added after import so the skill can serve vertical feeds. One canvas per project (`CANVAS` in the
timeline), with `--canvas` for a second ratio. `assets/engine/canvas.js` holds the presets, the 9:16
safe band (derived from the band `scenario-formats` and `scenario-video-ads` compose to, reading
their 6 to 13% per side as 6% left and 13% right, where the action rail sits), the per-canvas
timeline filter and `plateFit`. The HUD, the house subtitle and the scene template lay out inside
`E.SAFE`; every portrait-only behavior is gated off landscape.

Verified headless (Playwright's Chromium, software WebGL) with synthetic audio, lyrics and a
synthetic footage clip (frames, matte, tracking): landscape stills of both template branches
(footage and 3D) and the HUD, including a 150-character lyric line, are pixel-identical to the
pre-change engine at scales 1 and 0.5. Portrait and square stills were checked by eye with the safe
band outlined, and the error paths (bad canvas, bad timeline tag, an `--only` with nothing to
render) fail fast. `canvas.js` has a unit suite. Two plan-only application tests (portrait only;
both ratios) passed with notes.

A live application test then produced a full 1080p60 portrait video end to end (a 2:14 song, 24
style frames, 27 clips, 9 section agents, about 15k CU) and passed with notes. It found the portrait
subtitle running into the HUD counters, a `crop` that stretched plates, a `--chant` window with no
end, transcription passes overwriting each other, `still.mjs` keeping a stale sheet, and the doc
gaps behind a mic-covered lip-sync retake, the 720p-only cost anchors and a rejected reference crop.
All are fixed; `motion_library.md` §10 notes one production behind its portrait rules.

## What the record does not cover

- The skill is the creator's own document, not distilled here, so it does not follow the house
  layout for recipe skills: its `references/lessons.md` plays the Common mistakes role.
- Costs are the production's observed relative prices, not live quotes.
- The engine and scripts need Node with Playwright, ffmpeg and a Python environment
  (`scripts/scaffold.sh` builds it); the matte tool needs macOS (Apple Vision).
- Tests cover the dependency-light scripts and `canvas.js`; the rest need the full environment and
  generated footage.

## Supply chain

What the setup and analysis scripts fetch, and how each source is pinned:

- **npm**: exact direct versions and a v3 lock with integrity hashes, installed with
  `npm ci --ignore-scripts`.
- **Python**: `assets/python/<platform>.txt` pins every package, transitives included, by version
  and SHA-256, wheels only. Installing builds nothing, so no build backend or compiler toolchain is
  fetched. Each run rebuilds `.venv` from the lock alone, with no `ensurepip`, so no unlocked pip.
  Only macOS arm64 and Linux x86_64 (manylinux 2.28, so glibc 2.28+) have locks: on Linux aarch64,
  `demucs` needs `sphn`, which has no wheel there, and its source build fetched a Rust toolchain and
  failed.
- **beat-this**: PyPI 1.1.0. Its provenance attestation names CPJKU/beat_this commit
  `ad7974846029835307ba19a3d5cefbf40b243041` (tag v1.1.0), and the wheel's package files are
  identical to that commit. uv refuses a Git requirement in hash-checking mode, so the attested
  wheel is how the commit is pinned.
- **Fonts**: google/fonts at one commit. Each file the scaffold downloads, and its family's
  `OFL.txt`, is checked against SHA-256. A mismatch removes the download and stops the scaffold.
  Files already in `assets/fonts/` are kept as they are, unchecked.
- **beat_this checkpoint**: `audio_analysis.py` downloads `final0` once into `models/`, checks its
  SHA-256 on every run, and passes the local path, which beat_this loads with `weights_only`. Given
  only the name, beat_this would fetch it unverified and unpickle it.
- **Whisper**: `lyrics_align.py` loads `Systran/faster-whisper-large-v3` at a fixed Hugging Face
  commit.

Regenerate the locks after any change to `requirements.in`, with uv 0.13.0: run the command in each
lock's header, moving `--exclude-newer` to the date you resolve on. The offline checks in
`tests/scenario-kinetic-music-video/test_python_lock.py` run in `pnpm test`.
`.github/workflows/kinetic-locks.yml` re-resolves both Python locks to prove they reproduce, then
installs each on its platform and imports the tools' modules. It also installs the npm lock with
`npm ci --ignore-scripts` and imports its three packages.

Verified on 2026-10-29, with no Scenario calls:

- The real scaffold ran in a `node:22-bookworm` container (linux/amd64, uv 0.13.0) and natively on
  macOS arm64: fonts, licenses, `npm ci`, the hashed Python install, every import, and
  `audio_analysis.py` on a synthetic 120 BPM click track (read back as 120 BPM).
- A tampered checkpoint was rejected and removed. The test suites cover a tampered font.
- The scaffold's test suite checks the platform choice, the hashed wheels-only install, and that a
  font mismatch installs nothing.

Remaining gaps:

- `uv venv --python 3.11` downloads a managed CPython when none is installed. uv verifies it against
  checksums built into uv, but uv itself, Node, npm, ffmpeg, Chrome, and swiftc are the user's.
- Demucs downloads `htdemucs` weights from `dl.fbaipublicfiles.com`, checked only against the short
  hash prefix in the file name, then unpickles them.
- The Whisper commit pins which files are fetched; whether huggingface_hub verifies their content
  was not checked.
- MediaPipe's legacy solutions ship their models inside the hashed wheel; nothing else downloads at
  run time as far as the scripts show.
