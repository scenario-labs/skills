#!/usr/bin/env bash
# Scaffold a kinetic music-video project in the CURRENT directory.
# usage: bash <skill>/scripts/scaffold.sh /path/to/master.mp3
# Needs: node >= 20, python3.11 via uv, ffmpeg/ffprobe, Google Chrome (Playwright drives it headless with GPU).
# macOS: Xcode command-line tools (swiftc) to build the Apple Vision matte tool. Elsewhere mattes come from another source.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
MASTER_SRC="${1:?give the path to the song master}"
mkdir -p audio engine/scenes engine/data assets/fonts assets/refs assets/gen assets/clips assets/video assets/audio_slices assets/brand analysis out tools
# the song may already sit at audio/master.<ext> (cp refuses identical files and set -e would abort)
[ "$MASTER_SRC" -ef "audio/master.${MASTER_SRC##*.}" ] || cp "$MASTER_SRC" "audio/master.${MASTER_SRC##*.}"
cp -R "$SKILL/assets/engine/." engine/
cp "$SKILL/scripts/"*.py "$SKILL/scripts/"*.mjs "$SKILL/scripts/"*.swift "$SKILL/scripts/prep_clip.sh" tools/
[ -f engine/timeline.js ] || cp "$SKILL/assets/timeline.template.js" engine/timeline.js
cp -n "$SKILL/assets/scene.template.js" engine/scenes/_template.js || true
cp -n "$SKILL/references/engine_api.md" ENGINE_API.md || true
cp -n "$SKILL/references/agent_brief_template.md" AGENTS_BRIEF.md || true

# subject matte tool (Apple Vision foreground instance mask, ~0.1 s/frame, free)
if [ "$(uname)" = "Darwin" ] && command -v swiftc >/dev/null; then
  [ -x tools/matte ] || swiftc -O tools/matte.swift -o tools/matte || echo "note: swiftc failed (an unaccepted Xcode license is the usual cause: sudo xcodebuild -license accept). Mattes: Scenario background removal + tools/matte_keyed.py, or tools/matte_fallback.py."
else
  echo "note: no swiftc/macOS, so tools/matte was not built. Provide mattes as assets/video/<clip>/m_#####.png another way."
fi

# fonts (OFL, from google/fonts). The engine's index.html declares these families. Add project fonts the same way.
B=https://raw.githubusercontent.com/google/fonts/main/ofl
for p in "archivo/Archivo%5Bwdth,wght%5D.ttf:Archivo-VF.ttf" "archivoblack/ArchivoBlack-Regular.ttf:ArchivoBlack.ttf" "anton/Anton-Regular.ttf:Anton.ttf" \
  "jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf:JetBrainsMono-VF.ttf" "doto/Doto%5BROND,wght%5D.ttf:Doto-VF.ttf" "blackhansans/BlackHanSans-Regular.ttf:BlackHanSans.ttf" \
  "unbounded/Unbounded%5Bwght%5D.ttf:Unbounded-VF.ttf" "instrumentserif/InstrumentSerif-Italic.ttf:InstrumentSerif-Italic.ttf" "instrumentserif/InstrumentSerif-Regular.ttf:InstrumentSerif.ttf"; do
  [ -f "assets/fonts/${p##*:}" ] || curl -fsSL "$B/${p%%:*}" -o "assets/fonts/${p##*:}"
done

# JS deps
[ -f package.json ] || npm init -y >/dev/null
npm i -s three@0.170.0 playwright@1.49 opentype.js >/dev/null

# Python env (audio analysis, lyric alignment, footage prep, tracking, sync checks)
export UV_NATIVE_TLS=1 # uv ignores the system certificate store by default and fails behind a TLS-inspecting proxy
uv venv .venv -q --python 3.11
.venv/bin/python -m ensurepip >/dev/null 2>&1 || true
uv pip install -q --python .venv/bin/python faster-whisper librosa soundfile numpy scipy demucs torch torchaudio opencv-python "mediapipe==0.10.14" matplotlib pillow "git+https://github.com/CPJKU/beat_this.git"
echo "scaffolded. master: audio/master.${MASTER_SRC##*.}"
echo "next: .venv/bin/python tools/audio_analysis.py audio/master.${MASTER_SRC##*.}"
