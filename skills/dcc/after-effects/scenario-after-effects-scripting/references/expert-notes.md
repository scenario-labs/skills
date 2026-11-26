# Expert notes: scripting and automation

Principles and judgment by source, with timestamps. [added] marks rules this skill adds from live
tests on After Effects 27.0. Videos from 2016 to 2022 show retired tools (ExtendScript Toolkit,
Media Encoder for H.264); their patterns hold, their UI does not.

## Joey Korenman, School of Motion: Render-Bot (uo5k4_vu5Vk, 2018)

- Two levels of automation: a template a person fills (Essential Graphics, `.mogrt`) and a robot
  that reads rows and renders with no person (00:00:35, 00:01:12). Pick by volume: a few ad-hoc
  versions edited by people, or dozens to hundreds from a sheet (00:13:55, 00:14:28).
- Bake the rules into the template: one-line versus two-line layout, a visible warning above the
  character limit, all caps through the Character panel instead of asking editors (00:03:52,
  00:06:42).
- Expose only what changes (00:02:01). Essential Graphics warns when an exposed property is driven
  by an expression; the control is dead unless the expression reads it (frame 00:03:50).
- Data columns must equal layer names, spelling and case (00:19:20). Validate in the sheet, for
  example a red format above 40 characters (00:16:06).
- A `render status` column with `ready` gates the bot, because forms write rows before data is
  complete (00:30:29). Clean data in a second tab that references the form tab (00:29:57).
- Choose the output module by name as part of the job; forgetting it produced 26 AIFF files
  (00:22:39).
- Deterministic variety: a precomp of one-frame variants driven by Time Remap seeded from the name
  length (00:25:59).
- Precomps with empty space distort attachment layouts; crop them or use negative padding
  (00:36:34).
- Google Sheets polling never goes below 3 minutes (00:38:13).

## Sergei Prokhnevsky, ukramedia: Excel CSV batch render (Ov4Zd-Mgmbo, 2021)

- Re-versioned 20 to 40 times a week: move the variable content into a table, one row per render
  (00:00:00 to 00:08:09).
- Make the template responsive before automating (00:01:38).
- Controlled values (`None` hides a row, fixed time-zone codes) instead of free text remove the top
  cause of rework (00:03:49 to 00:05:29). Scripted: `AEX.batch.validate` with `allowed` lists
  [added, live 27.0].
- The sheet is a job ledger: `Status` Ready or Done, `File Name`, per-field columns; set a row back
  to Ready to rerun (00:06:56 to 00:11:57).
- Write a per-run report so the sheet can be refreshed and finished rows show Done (00:11:25 to
  00:11:57). Scripted: `status.csv` from `AEX.batch.writeCsv`, one row per data row [added, live
  27.0]. Render and output templates are picked per machine because installed codecs differ
  (00:10:20).
- A script plus a CSV runs on old versions where Essential Graphics media replacement does not
  (00:00:32); in 2026 both routes are available.

## Video automation company team: responsive MOGRT (SkIOeqJEKD0, 2025)

- A template must survive 3 or 303 characters, any brand color, font and duration (00:00:00,
  00:00:31).
- `sourceRectAtTime` plus a Padding slider is the whole responsive box (00:01:04).
- Protected regions keep in and out animations intact when an editor changes the duration
  (00:01:46). Scripted: `MarkerValue.protectedRegion = true` [added, live 27.0].
- Expose text color through a Fill effect, not the text fill (00:02:30).

## Nate Lovell, NT Productions (DTBtfFiyjNU 2022, 6AWYsTC76gs 2021, gGFjkzX6y6g 2019)

- Match names make scripts language independent:
  `property("ADBE Transform Group").property("ADBE Position")` (DTBtfFiyjNU 00:31:59; 6AWYsTC76gs
  00:19:26 shows the display-name trap).
- One undo group per run (DTBtfFiyjNU 00:37:25). Nested groups collapse into the outer one [added,
  live 27.0].
- Guard the input first: `activeItem instanceof CompItem` (DTBtfFiyjNU 00:27:15). An agent passes
  the comp name in `ARGS` instead of relying on the active item [added].
- Check `File.exists` before `importFile` (DTBtfFiyjNU 00:40:09). A missing path throws "Path is not
  valid" [added, live 27.0].
- Reproduce the manual action once, copy the resulting expression or value into the script
  (6AWYsTC76gs 00:18:22).
- Read and write JSON with open, read or write, close; an unclosed file stays locked (gGFjkzX6y6g
  00:07:11). ExtendScript in 27.0 has no `JSON` object: use a bundled parser (`AEK.json`) [added,
  live 27.0].

## Code and Motion (a90H-Pf61LQ 2019, UutXfHp9KDg 2019)

- VS Code with Adobe's ExtendScript Debugger replaces the retired ExtendScript Toolkit (a90H-Pf61LQ
  00:00:00).
- `jsconfig.json` with `target ES3`, `noLib`, `checkJs` plus type definitions catches invented
  members before a run (a90H-Pf61LQ 00:03:40 to 00:05:00). `ae_check.py` plays that role for an
  agent [added].
- Guard against an empty selection; wrap big actions in one undo group (UutXfHp9KDg 00:16:08,
  00:17:27).

## Workbench (vAenMHvAHQI, 2016)

- `aerender` renders a saved project while the artist keeps working; the queue lives in the saved
  project (00:00:38, 00:02:53).
- Wrap the long command in a small shell script that takes the project path (00:01:44).

## AI script-writing panel tutorial (aescripts + aeplugins, s6SjIehPGhc, 2026)

- Keep requests small and specific, name exact counts, formats and durations, iterate, and review
  the code before production use (frame 00:00:30, 00:00:44).
- Save every working script to a library with a name and a description (00:01:40).

## Docs (aerender, scripting guide, nexrender README)

- `aerender` with no `-comp` renders the whole queue as saved and honors only `-project`, `-log`,
  `-v`, `-mem_usage`, `-close` (aerender doc). Live: only QUEUED items render, DONE items are
  skipped [added, live 27.0].
- `-s` and `-e` are frame numbers, `-e` inclusive; `-reuse` renders in a running instance; `-close`
  defaults to DO_NOT_SAVE_CHANGES (aerender doc). Consequence: DONE never reaches the saved `.aep`,
  so a rerun renders the whole queue again; resume from verified files [added, live 27.0].
- `-mfr ON|OFF max_cpu_percent` (1 to 100, ignored when OFF) sets Multi-Frame Rendering per run; MFR
  is on by default since 22.0. `-continueOnMissingFootage` renders color bars in place of missing
  footage (aerender doc).
- Multi-machine rendering: image sequences only, Skip Existing Files on, one output module per item,
  assemble afterwards (aerender doc).
- Fonts, effects and encoders must exist on every render machine; copy plug-ins to each, never share
  them over the network (aerender doc). A missing font shows as "Project has missing fonts" in the
  `aerender` log and as `isSubstitute` true after reopen [added, live 27.0].
- Truly headless on macOS: `aerendercore` inside the app bundle is undocumented; quit it with
  `app.quit()`, kill hung instances by PID after a timeout, cap concurrency (three in the reported
  setup) (Adobe Community answer, scripts without GUI on macOS).
- Comps using the Cinema 4D renderer can render nothing under `aerender` ("Couldn't find a result
  file"); Classic 3D and Advanced 3D are fine (nexrender README).

## Template systems compared (named factually)

| Tool                             | What it is                                 | What it adds over a script plus `aerender`                                                                                                                                                                                                                                          | Deciding condition                                                             |
| -------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Templater                        | Paid After Effects panel and bot           | Google Sheets, JSON or form data, `Templater Settings` effect per layer, Scale factor and Attachment layout rules, replicate one comp per row, bot polling a `render status` column, Media Encoder handoff (uo5k4_vu5Vk 00:17:10 to 00:39:22)                                       | Artists who want a panel and a layout engine without code                      |
| Hosted render service            | Hosted service                             | Upload an After Effects template, feed rows by spreadsheet or API, renders in the cloud (vendor blog, sources.md)                                                                                                                                                                   | No render machines in house, API-driven volume                                 |
| nexrender                        | Open-source Node tool                      | JSON jobs (`template.src`, `composition`, assets by `layerName`, `data` assets set any property by value or expression, `script` assets with `NX.get`), copies the project to a temp folder, runs `aerender`, server and workers for a farm, post-render actions (nexrender README) | Developers running a farm from code; each worker needs After Effects installed |
| Custom ExtendScript (this skill) | `AEX.batch` plus the bridge and `aerender` | Full control, report per row, no extra license                                                                                                                                                                                                                                      | Studio pipelines with a developer, agents                                      |

For nexrender on After Effects 2023 and later, set `outputModule` (for example
`H.264 - Match Render Settings - 15 Mbps`), `outputExt` and `settingsTemplate` in the job;
`aerender` often renders nothing without a configured output module (nexrender README).

## Platform status (docs and version deltas)

- ExtendScript (ES3) with ScriptUI stays the dependable path in 26.x and 27.0; Adobe says standalone
  scripts are expected to keep working through the UXP transition.
- UXP: public beta in After Effects (Beta) 27.1 (build 27.1.0.045, UXP 9.4, UXP Developer Tool 2.4,
  `ae-quick-starter`). Hybrid UXP plugins with native C++ are not supported yet; general
  availability with hybrid is targeted for Q2 2027.
- CEP: disabled by default from December 2028, removed from new versions starting December 2029.
- C++ SDK: the 27.0 SDK exists (its announcement date differs between Adobe sources); it builds
  native effects and AEGPs, not pipeline scripts.
- Running scripts from outside: `afterfx -r file.jsx` on Windows; AppleScript or JXA `DoScriptFile`
  on macOS needs the Automation permission and timed out in the live tests without it; the mailbox
  bridge of scenario-after-effects-expert needs none.
