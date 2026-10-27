# scenario-kinetic-film: maintainer notes

How the skill was built, why it makes its choices, and how far it was verified. For the agents and
humans working on the skill; SKILL.md does not link it.

## Origin

Added on 2026-10-27. Its author first hand-wrote a kinetic-type film as code. Version 1 matched a
reference reel's cut timing but measured 81% still frames and a 6 s hold. Version 2 was rebuilt
after measuring three high-energy motion design reels frame by frame (still share, holds, motion,
cuts, color flips). The skill turns version 2's hand-written scenes into 14 blocks driven by a spec,
plus the render, sound and check pipeline. Kaiju Postal, a fictional game teaser written from a
fresh brief, tested that the blocks generalize.

## Choices

- **Fonts are fetched, not shipped.** `get_fonts.sh` pins one google/fonts commit and checks each
  file's sha256 (the three variable fonts and their OFL texts). Shipping them would add about 1 MB
  of binaries and six SKILL.md links. A missing or wrong font fails the boot with a message.
- **The film boots or says why, at once.** `main.js` checks the spec (`validate.js`) before the
  `Film` constructor, loads fonts with `allSettled`, and catches any boot error. It always sets
  `window.__ready`, with the reasons in `window.__problems`, so info.mjs fails in seconds instead of
  a 120 s timeout, and the Python scripts print the reason instead of a traceback.
- **The spec checks accept custom blocks**: any subclass of `Scene`. Warnings go to `console.warn`,
  since the scripts count `console.error` as page errors. There is no overlap warning: blocks
  overlap on purpose (the tour's collapse grows into its logo line).
- **The engine and examples are not reformatted** (`.prettierignore`): the Counters block shows the
  film's own source and `{lines}` counts it, so a reflow would change what renders. New engine files
  are appended to main.js's source list, so its first two entries stay spec.js and blocks.js.
- **The logo sanitizer is an allowlist** of SVG drawing elements. Comments and processing
  instructions go too: a PI whose data holds `>` ends early in the HTML parser and lets markup
  through. References to other hosts are dropped from `href`, `url()` in attributes and style, and
  `<style>` blocks; fragments and same-folder paths stay.
- **Only new_film.sh refuses to overwrite**: a non-empty folder needs `--force`, which also finishes
  a scaffold that stopped part way (the exit message prints the command) and refreshes the engine
  while keeping spec.js, custom.js, audio/, art/ and out/. mix, render and finish replace their
  outputs, so the 1080p check run and the 4K master share out/final.
- **holds.py reads at 60 fps, like dyn.py.** It used to divide frame counts by 60 at the source's
  own rate, so a 30 fps reference reported holds at half their length. Units stay px per 1/60 s.
- **The end card starts at the Logo block or 4.5 s before the end, whichever is earlier.** The 4.5 s
  rule alone counted the last second of a long Logo block (11 beats at a calm 120 BPM is 5.5 s) as
  holds. At 172 BPM nothing changes, so the Kaiju Postal numbers stay comparable.
- **The HUD and the Rewind timecode count frames at `spec.fps`**, not a fixed 60.
- **main.js fetches the film's source files one at a time**: a burst of requests once had a
  connection reset by `python3 -m http.server`, the documented preview server.
- **Python 3.12.** numpy 2.5.4 needs it. `assets/requirements.txt` pins exactly what
  `tests/requirements-ci.txt` locks (a test checks). Dependabot bumps both in one Python group; a
  bump of the shipped file releases only under a `fix` PR title.
- **Playwright 1.64.1, locked**, the same pin and integrity as the music-video skill's lock (a test
  checks), installed with `npm ci --ignore-scripts`.
- **Scripts were rewritten for reading** (one statement per line, usage on a bare call, messages
  instead of tracebacks). Outputs were compared against the earlier versions on the same synthetic
  inputs: mix.py's WAV, post.py's frames (with and without grain), dyn.py, holds.py at 60 fps,
  audit.py and montage.py came out identical, and beat_grid.py's JSON matched on 10 tracks.

## Open issues

- **beat_grid.py reports downbeats about 70 ms early** on synthetic kick-led drums (68 to 80 ms at
  120 to 172 BPM, two kick shapes); a reviewer measured up to 119 ms with a longer kick. The onset
  envelope lags the kick. A constant shift fit one kick and missed another, so no fix shipped. A fix
  should refine the phase on a fine envelope and be tested on generators it was not tuned on.
- **Off-beat hats over a long kick pull the grid half a beat off** (+100 to +180 ms at 120 to 172
  BPM), and `grid_strength` still reads 1.0. A kick-band half-beat check is the likely fix, flipped
  only past a margin.
- Both are pre-registered as expected failures in `tests/scenario-kinetic-film/test_beat_grid.py`: a
  fix turns them into unexpected successes, which fail the suite until the decorators go.
- Kaiju Postal's `music.offset` (7.95) was measured with this tool, so it carries the same bias.
- `grid_strength` saturates at 1.0 on every synthetic track, wrong grid or not.
- Drop candidates cluster around a drop (two bars after against one bar before), and the highest
  `rise` is not always the drop itself.
- rectify.py's screen mask is not exercised by its test: RANSAC rejects the screen's changing
  content on synthetic footage anyway.

## Verification record

- **Author runs (macOS, Apple silicon, 36 GB, Google Chrome, ffmpeg 7.1)**: Kaiju Postal passed
  finish.py with 24% still frames before the end card, no hold over 0.6 s, median motion 4.2
  px/frame and 12.5 cuts per 10 s. Its music, a 16-sound kit and two key arts were generated through
  the Scenario MCP server; none of them ship. Renders took the times render.md gives.
- **This repository's suites** (`tests/scenario-kinetic-film/`, CI on Ubuntu with ffmpeg 6.1 and
  8.0, no browser): every Python script on synthetic lossless media, the engine helpers, spec checks
  and sanitizer under node and jsdom, and the compositor's seek-order determinism with recording
  canvases. Each new test was seen to fail on a broken copy of the code.
- **Opt-in suites, run on macOS with Chrome before merging**: `KINETIC_FILM_PLAYWRIGHT_DIR` (and
  optionally `KINETIC_FILM_FONTS_DIR`) runs browser.test.ts; `KINETIC_FILM_NETWORK=1` downloads the
  real fonts. browser.test.ts boots the tour with no problem, takes stills and streams render
  samples. It checks a frame is identical whatever was seeked before. It fails fast on a bad style,
  a spec.js syntax error and missing fonts.
- **A scaffold-to-finish run on macOS, 2026-10-27**: new_film.sh with the real npm, uv (Python
  3.12.9) and font download, then a synthetic sound kit, mix.py, render.py at 1080p (889 frames, 2
  workers, 3 min 51 s) and finish.py on the starter film. Every per-file gate passed, the hardware
  decode included. The motion gates failed: 43% still frames and 2.24 px/frame. The starter is a
  shape to fill in, and its stills match the earlier engine's to within GPU noise.
- **Not covered**: no fresh-agent run (`/skills:validate`) yet; no render on Linux or Windows; no
  real generated music through the refactored scripts; no 4K render of the refactored pipeline.
- Dependabot bumps of `assets/npm` or `assets/requirements.txt` deserve a live `/skills:validate`.
