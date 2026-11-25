# Critique: judging a delivery before it leaves

Run the numeric checks first, then read ONE contact sheet. A passing number never excuses a wrong
frame, and a good-looking frame never excuses a failed number. In a 32 bpc project, frames saved
with `saveFrameToPng` read at one tenth of their value: judge render queue frames.

## 1. Numbers (from jobs and scripts)

| Check              | Pass                                                                                                                                                                            | How                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Project color      | bit depth, working space, linearize, blending and engine equal the plan                                                                                                         | `AEX.delivery.state()`                                                                     |
| Working space name | in `listColorProfiles()`; never "None" by accident                                                                                                                              | `setColor` throws otherwise                                                                |
| OCIO project       | 32 bpc read back (16 is refused, 8 is kept silently); config name recorded; a person confirmed working, display and media spaces in the GUI                                     | `state()` and the person's answer                                                          |
| Render             | status DONE for every item; each output module summary matches the plan (format, channels, depth, straight or premultiplied, audio)                                             | `AEX.delivery.render` result                                                               |
| Codec and profile  | ProRes 4444 `yuva444p12le` only with alpha; opaque master ProRes 422 `yuv422p10le`; web H.264 High `yuv420p` from ffmpeg (the After Effects template writes Main)               | `delivery_check.py`                                                                        |
| Size, rate, length | width, height, fps and frame count equal the spec; duration within one frame                                                                                                    | `delivery_check.py`                                                                        |
| Alpha              | present when asked (`yuva*`, `rgba`), absent otherwise; PNG frames straight                                                                                                     | `delivery_check.py`, sheet                                                                 |
| Color tags         | primaries, transfer and matrix `bt709` for HD and web; range `tv` unless the spec says full; an SD-size master reached bt709 by a matrix conversion, never a re-tag             | `delivery_check.py`, the encode line                                                       |
| Data streams       | no timecode (`tmcd`) or other data stream in a web MP4                                                                                                                          | `delivery_check.py no_data`                                                                |
| Fast start         | moov atom before mdat on web MP4                                                                                                                                                | `delivery_check.py faststart`                                                              |
| Audio              | 48 kHz, codec and channels per spec; loudness within the target tolerance; true peak at or under the ceiling                                                                    | `delivery_check.py audio`                                                                  |
| File size          | under the platform cap (App Store previews: 500 MB)                                                                                                                             | `delivery_check.py max_mb`                                                                 |
| Sequence           | starts at the agreed number, no gaps                                                                                                                                            | `delivery_check.py sequence_start, gaps`                                                   |
| Banding            | median flat run 1 to 2 px and widest run 16 px or less, on a dark or gradient row of a full-size frame of the encoded file                                                      | `band_check.py --max-run 16`                                                               |
| Levels             | black floor and white ceiling where the grade intends; broadcast 16 to 235 at 8 bits, 64 to 940 at 10, 256 to 3760 at 12; with grain, 0.01 % or less of the worst frame outside | `delivery_check.py levels` (reads the file's bit depth; `max_out_pct`) on the encoded file |
| Protected colors   | every named color within delta E 5 and 4 hue degrees between grade off and on, and between source and delivered file; chroma change read                                        | `color_protect.py` (procedures 4b)                                                         |
| Render settings    | Best quality, Full resolution, Use No Proxies                                                                                                                                   | `AEX.delivery.render` `renderSettings`                                                     |
| Grain              | Viewing Mode Final Output (3); grain over the whole frame, titles included or Match Grain on them                                                                               | effect values, sheet                                                                       |
| Templates created  | each one prefixed and listed in the report                                                                                                                                      | the job's return value                                                                     |
| Safe areas         | every title row `ok` for title safe and for each platform box                                                                                                                   | `AEX.delivery.safeCheck`                                                                   |

## 2. The contact sheet

One sheet, every deliverable:

- Alpha over a checkerboard: no dark fringe (premultiplied read as straight), no light halo, no lost
  soft edges.
- Each aspect ratio side by side: subject and titles inside, nothing important cut by a center crop.
- The grade with titles: brand colors untouched (numbers from `color_protect.py`), skin and neutrals
  plausible, no clipped sky.
- A contrast-stretched gradient crop at 1:1: no visible steps.
- Frames decoded with the file's matrix and `in_range=tv` (procedures.md, section 10), not ffmpeg's
  default conversion.
- First, middle and last frame of each file: no black first frame, no frozen last frame.

## 3. Verdict

- PASS: all numbers pass and the sheet shows no defect.
- FIX: list each failed row with expected and measured values, the cause and the fix (from the
  Common mistakes table in SKILL.md), then re-render only what changed.
- Report to the person: file list, check report, assumptions (color spaces assumed for inputs,
  loudness target chosen, safe boxes used).
