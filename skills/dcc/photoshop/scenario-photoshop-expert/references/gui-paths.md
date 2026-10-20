# GUI paths (steps no script does)

Menu and panel paths for what the `ps_run` channel cannot do or should not do on the user's behalf.
Give the user the exact path and wait for them; never click screen coordinates or bring Photoshop to
the front. Paths are from Adobe documentation or the cited videos; none is tested by this skill's
live suites. Names follow Photoshop 2026 (27.x) on macOS; on Windows read Ctrl for Cmd.

Specialists keep the GUI paths of their own domain (Select and Mask refine, Generative Fill and
Expand as manual alternatives, brush work, Camera Raw controls).

## Setup the user does once

- **Allow automation (exit 6):** System Settings > Privacy & Security > Automation > the terminal or
  agent app > Adobe Photoshop on.
- **Developer Mode (to copy Action Manager code):** Settings (Preferences) > Plugins > Enable
  Developer Mode, then restart Photoshop.
- **Copy As JavaScript:** record the step as an Action, then Actions panel flyout menu > Copy As
  JavaScript. Paste the descriptors into a job body.

## Documents and viewing

- **Bring a document to the front:** click its tab, or the Window menu > the document's name. Ask
  the user; never switch documents from a job.
- **Judge at 100%:** View > 100% (Cmd+1); fit to screen is Cmd+0 [a7E4HlrAc3w 04:10].
- **History:** Window > History. A Scenario edit shows as one state named "Scenario: <action>".
  Clicking the state above it reverts the edit; a new action then discards the states below.
- **Save:** the user's own call (File > Save, or File > Save a Copy). The agent writes copies only.

## Layers the user may want after a round trip

- **Edit a placed result:** double-click the smart object thumbnail (opens its contents), or Layer
  > Smart Objects > Replace Contents to swap the file and keep the transform.
- **Rasterize for pixel tools:** Layer > Smart Objects > Rasterize. Some pixel tools and many
  Actions need a pixel layer; work on a duplicate (Cmd+J) so the smart object stays.
- **Stamp visible:** Cmd+Opt+Shift+E merges what is visible into a new pixel layer and leaves the
  stack intact [6vsnsS92gKc 11:57].
- **Layer Cleanup (27.6 and later):** Layers panel > Layer Cleanup: deletes empty layers and renames
  layers by content, for the whole document or the selected layers [7U4GERm0HnU 20:30]. Offer it
  before a layered handoff; it is not scriptable.

## Actions

- **Panel:** Window > Actions. Since 27.6 it opens on the redesigned panel with built-in actions;
  the classic view holds record, edit and step lists [6vsnsS92gKc 11:24].
- **One History state per action:** Actions flyout > Playback Options > Create single history state
  [6vsnsS92gKc 11:24]. The agent's own jobs already do this.
- **Load a set:** Actions flyout > Load Actions, then pick the `.atn` file. Loading one from a
  script is not verified on 27.11, so ask the user to load it.
- **Play from the top:** select the action's name, not a step inside it; playing from a step starts
  the action midway [MQDF-UW5-Uk 07:42].
- **Read before playing:** expand the action and look for Save, Save As, Close or Flatten steps.

## Batch and bulk export

- **Batch:** File > Automate > Batch. Source Folder or Opened Files; Errors: Stop For Errors, so a
  failing file halts the run [4oAcuL0Q7Ec 06:52]; Destination Folder with Override Action "Save As"
  Commands on [4oAcuL0Q7Ec 07:25]. Destination Save and Close overwrites the originals: avoid it.
- **Image Processor:** File > Scripts > Image Processor: JPEG, PSD and TIFF copies with resize and
  sRGB conversion in one run, into subfolders, without overwriting.
- **Template variants (Variables and Data Sets):** Image > Variables. That work belongs to the
  key-art specialist.

## Generative features as manual alternatives

The toolkit's channel does not reach Photoshop's own generative tools except through an Action the
user recorded; that route is not tested here. When the user prefers them, name the path and land
nothing from the agent's side:

- Generative Fill: make a selection, then the Contextual Task Bar > Generative Fill.
- Generative Upscale: Image > Generative Upscale [UorIb_rGZuc 08:49].
- Image to video: Photoshop sends the frame to Adobe's web app, outside Photoshop. The Scenario
  route is `scenario-video` with an exported frame.
