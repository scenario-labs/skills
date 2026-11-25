# GUI paths: scripting and automation

For a person, or a computer-use agent, doing the same steps by hand. macOS shortcuts first, Windows
in brackets.

## Scripts

- Run a script: File > Scripts > Run Script File. Rerun the last one: Cmd+Option+Shift+D
  (Ctrl+Alt+Shift+D).
- Allow file writes and network: After Effects > Settings > Scripting & Expressions > Allow Scripts
  to Write Files and Access Network (Edit > Preferences > Scripting & Expressions). Older docs place
  it under General.
- Install a script: copy the `.jsx` into the application's `Scripts` folder; it appears in File >
  Scripts after a restart.
- Install a ScriptUI panel: copy it into `Scripts/ScriptUI Panels` (or File > Scripts > Install
  ScriptUI Panel); it appears at the bottom of the Window menu after a restart.
- Startup and Shutdown scripts: `Scripts/Startup` and `Scripts/Shutdown` (the user Scripts folder
  works without admin rights) run in alphabetical order.
- Stop a running script: Esc (Cmd+period on macOS).
- Edit and debug: VS Code with Adobe's ExtendScript Debugger extension; select After Effects as the
  target in the status bar.

## Render queue

- Add a comp: Composition > Add to Render Queue (Cmd+M / Ctrl+M).
- Render settings and output module: click the underlined template names in the Render Queue panel.
- Save a template: Edit > Templates > Output Module (or Render Settings) > New; the same dialog
  lists the installed names that a script may use.
- File name template: in Output To, the menu next to the file name offers templates such as
  `[compName].[fileExtension]`; custom ones are typed as tokens.
- Queue in Media Encoder: Composition > Add to Adobe Media Encoder Queue (or File > Export > Add to
  Adobe Media Encoder Queue).
- Multi-machine: Render Settings > Skip Existing Files (allow multi-machine rendering), image
  sequence output, one output module per item.
- 3D renderer before an `aerender` batch: Composition > Composition Settings > Advanced > 3D
  Renderer (nexrender README); switch a Cinema 4D comp to Classic 3D or Advanced 3D.

## Essential Graphics and MOGRT

- Window > Essential Graphics. Pick the comp as Primary, drag properties into the panel, name and
  group them.
- Media replacement: drag a footage layer into the panel.
- Protected region: set the work area, then Composition > Responsive Design - Time > Create
  Protected Region from Work Area (also Create Intro, Create Outro: 15 % of the duration each), or
  double-click a comp marker, give it a duration and check Protected Region.
- Export: Essential Graphics panel > Export Motion Graphics Template; choose Local Templates Folder
  or a folder. Save the project first.
- Per-instance overrides: twirl a precomp layer open in the parent comp to Essential Properties and
  edit the values there.

## Duplicates and versions

- Duplicate a comp: Edit > Duplicate (Cmd+D / Ctrl+D) in the Project panel. Nested precomps stay
  shared; duplicate each precomp by hand, select the layer in the timeline, then Option-drag
  (Alt-drag) the copy from the Project panel onto it to replace its source.
- Replace footage: select the item, File > Replace Footage > File.

## Headless render

- `aerender` lives next to the application (`/Applications/Adobe After Effects <version>/aerender`,
  Windows `...\Support Files\aerender.exe`). Help: `aerender -help`.
- Watch folder: File > Watch Folder (render node on another machine picks up projects saved with
  Collect Files).
- Render-only node: Help > Sign Out, quit, create an empty `ae_render_only_node.txt` in the user's
  Documents folder or in `Adobe` inside the macOS Shared user folder (Windows: the Public Documents
  `Adobe` folder).
