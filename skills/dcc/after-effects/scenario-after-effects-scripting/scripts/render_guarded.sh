#!/bin/bash
# render_guarded.sh PROJECT.aep OUT_DIR MIN_FREE_MB [STALL_S] [LOG_DIR] [MANIFEST]: whole-queue aerender, for a plain shell
# pipeline. One comp at a time goes through `ae.py aerender` (scenario-after-effects-expert) instead: same definition of a failed render.
# A render has failed on any of: an error line, a non-zero exit, a missing output file, a movie that decodes short.
# Guards: 1. refuses to start under MIN_FREE_MB free on the output volume (exit 2);
# 2. stops aerender and its children when its log gains nothing for STALL_S seconds (default 120);
# 3. reads every item from the log ("Output To", "Duration", "Frame Rate"), then checks each file was written by this run
#    and decodes the span's frames; a sequence ("[####]") must have one file per frame;
# 4. MANIFEST (from AEX.batch.renderManifest: "path<TAB>frames" per queued output) adds the items that never started.
# Prints one line per output: "<name> <frames found> of <frames expected>", then "RESULT ok" or "RESULT failed: <why>" (exit 1).
set -u
P="$1"; OUT="$2"; MIN="$3"; STALL="${4:-120}"; LD="${5:-$OUT}"; MAN="${6:-}"
AER="${AERENDER:-$(ls -d /Applications/Adobe\ After\ Effects\ 20*/aerender 2>/dev/null | sort | tail -1)}"
mkdir -p "$OUT" "$LD"
free=$(df -k "$OUT" | awk 'NR==2 {print int($4/1024)}')
if [ "$free" -lt "$MIN" ]; then echo "RESULT failed: ${free} MB free on the output volume, ${MIN} MB needed"; exit 2; fi
LOG="$LD/aerender.log"; : > "$LOG"; STAMP="$LD/.render_start"; touch "$STAMP"; sleep 1
"$AER" -project "$P" -v ERRORS_AND_PROGRESS -log "$LOG" > "$LD/aerender.stdout" 2>&1 &
pid=$!; last=-1; idle=$(date +%s); why=""
while kill -0 "$pid" 2>/dev/null; do
  sleep 3
  n=$(( $(wc -c < "$LOG") + $(wc -c < "$LD/aerender.stdout") )); now=$(date +%s)
  if [ "$n" != "$last" ]; then last=$n; idle=$now; fi
  if [ $((now - idle)) -gt "$STALL" ]; then why="no log output for ${STALL} s, aerender stopped"; pkill -P "$pid"; kill "$pid"; fi
done
wait "$pid"; rc=$?
add() { why="${why:+$why; }$1"; }
# the log separates lines with carriage returns; the patterns match ae.py aerender's (case-insensitive)
TXT="$LD/aerender.txt"; cat "$LOG" "$LD/aerender.stdout" | tr '\r' '\n' > "$TXT"
errs=$(grep -iE "disk full|not enough (disk )?space|no space left|9988|output module failed|unable to write|could not write|can not create a file|error while writing|aerender error" "$TXT" | head -3)
[ -n "$errs" ] && add "$errs"
[ "$rc" != 0 ] && add "exit code $rc"
grep -qi "failed to write xmp" "$TXT" && xmp=" (the log says 'Failed to write XMP metadata': a disk-full sign)" || xmp=""
# one "path<TAB>frames" line per output started, frames from that item's Duration (H:MM:SS:FF) and Frame Rate
ITEMS="$LD/aerender.items"
# Duration reads H:MM:SS:FF (";" for drop frame) or, when the project displays frames, a plain frame count ("00060")
awk '/Duration: /{s=$0; sub(/.*Duration: */,"",s); sub(/[ \t]+$/,"",s); n=split(s,a,/[:;]/);
       if (n >= 4) { d=(a[1]*3600+a[2]*60+a[3]); f=a[4]+0 } else { d=0; f=s+0 } }
     /Frame Rate: /{s=$0; sub(/.*Frame Rate: */,"",s); split(s,b," "); r=int(b[1]+0.5)}
     /Output To: /{s=$0; sub(/.*Output To: */,"",s); sub(/[ \t]+$/,"",s); print s "\t" (d*r+f)}' "$TXT" > "$ITEMS"
if [ -n "$MAN" ]; then
  while IFS=$'\t' read -r mp mf; do
    [ -z "$mp" ] && continue
    grep -qF "$mp" "$ITEMS" || { echo "$(basename "$mp") 0 of $mf"; add "$(basename "$mp") never started"; }
  done < "$MAN"
fi
[ -s "$ITEMS" ] || add "the log names no output: nothing was rendered"
while IFS=$'\t' read -r f want; do
  [ -z "$f" ] && continue
  name=$(basename "$f")
  if [ -n "$MAN" ]; then m=$(awk -F'\t' -v p="$f" '$1==p {print $2}' "$MAN"); [ -n "$m" ] && want=$m; fi
  case "$f" in
    *\[#*)  # image sequence: count the files written by this run
      pre="${f%%\[#*}"; post="${f#*\]}"; k=$(find "$(dirname "$pre")" -maxdepth 1 -name "$(basename "$pre")*$post" -newer "$STAMP" 2>/dev/null | wc -l | tr -d ' ')
      echo "$name $k of $want"; [ "$k" -lt "$want" ] && add "$name: $k of $want frames written" ;;
    *)
      if [ ! -e "$f" ]; then echo "$name 0 of $want"; add "$name missing"; continue; fi
      if [ ! "$f" -nt "$STAMP" ]; then echo "$name 0 of $want"; add "$name not written by this run (an older file)"; continue; fi
      k=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$f" 2>/dev/null)
      case "$k" in ''|N/A) k=0;; esac
      echo "$name $k of $want"
      if [ "$k" -eq 0 ]; then add "$name decodes no frames$xmp"; elif [ "$k" -lt "$want" ]; then add "$name short: $k of $want frames$xmp"; fi ;;
  esac
done < "$ITEMS"
[ -z "$why" ] && echo "RESULT ok" || { echo "RESULT failed: $why"; exit 1; }
