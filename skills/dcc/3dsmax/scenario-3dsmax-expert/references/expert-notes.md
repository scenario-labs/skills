# Expert notes: operating 3ds Max through an agent

Principles from practitioners who drove 3ds Max with an agent through an MCP bridge, plus Autodesk's
own limits. Timestamps are from the public videos listed in [sources.md](sources.md). Lines marked
[added] are this skill's own rules.

## Forever Stu (Napalm_art), interior archviz, kBo57xFC3ic

- The agent is the operator. The human is the art director, and accuracy, taste and composition stay
  with the human [00:00:31, 00:29:50].
- MCP is only a bridge and does not replace a brief. A vague command makes the agent invent
  construction details and pick random modeling methods [00:02:40, 00:03:12].
- One huge task fails. Work in short complete stages, such as walls and openings, floor, windows and
  doors, then trims, furniture, materials, lighting and cameras. Each stage has a defined finished
  result and is approved before the next [00:03:12].
- Use one skill per stage. Merged instructions conflict [00:08:16].
- Technical rules (height, thickness, offset, segments, layer name) can be written down. Taste,
  color and lighting cannot, and his delegated lighting pass "was far from what I wanted"
  [00:14:06].
- Give a rule for choosing the tool, not a fixed method [00:11:24]. Say what the detail looks like,
  because "make it correct" explains nothing [00:13:02].
- Review in orthographic top views with control dimensions, never one attractive perspective. Every
  measurement must match the plan [00:08:50, 00:09:59].
- Corrections: marked screenshots and ONE structured list. When you fix something by hand, tell the
  agent what changed [00:08:50].
- After a local edit, check the neighbors [00:18:37].
- Do not make the agent model everything. Import finished models or use a generator, or the usage
  budget runs out [00:21:16].
- Do not build agent swarms: "If you can check something with your own eyes in two minutes, there is
  no reason to spend resources on a separate agent" [00:29:18].

## Arch Viz Artist, UuWmWAvB4Y0 (eight agent tasks in a Corona scene)

- The result is a starting point made of real editable objects, then refined by hand [00:03:16].
- Use the agent for setup-heavy steps (many materials, scatter lists, a light rig, a small tool).
  Keep composition and arrangement for yourself [00:03:47, 00:05:29].
- Attach a marked-up screenshot, with rectangles for assets and splines for areas [00:04:20,
  00:05:00].
- Constraints that worked: preserve geometry, organize on a new layer, keep it editable, do not
  render, do not switch the renderer [00:07:05; frame 00:03:04].
- Ask for editable structure (LightMix layers, scatter lists, layers) rather than baked results
  [00:07:37].
- Verification rule written into the prompt: activate each camera, capture it with Safe Frame
  visible, and "do not claim a shot is verified without viewing its capture" [frame 00:03:04].
- Timings: cameras 21 min, scatter 12, curtains 12, studio light about 10, material from a reference
  about 5, scene re-material about 15 (29 materials), a MAXScript tool 22 [various].
- Connection drops cost 25 of 35 minutes on the first task. Fix: update the bridge and re-run its
  start script [frame 00:02:01, 00:09:09].
- Proxies are not good agent targets. Make a mesh copy first [00:00:35].

## Arch Viz Artist, c3acjyR7j7E (two agents, same scene and prompt)

- Compare on the same scene, prompt and tools. Judge geometry, organization, material class and
  instruction fidelity, not polygon count [00:05:36].
- Ask for a summary plus the assumptions made where drawings were missing. It is a useful start for
  accuracy checks [00:04:28].
- Name the renderer. One agent used Physical Materials, the other simple V-Ray materials [00:05:02].
- Keep CAD reference layers, hidden, so a human can check alignment fast [00:03:53].
- Time is a quality dimension: 23 min against about 40 min for the same model [00:04:28].

## 3D GROUND, XpWCMn9Nboc and GQv8Y_8eiBU (bridge author)

- Layer 0 stays empty, and objects are separated by type [XpWCMn9Nboc 00:01:05].
- The agent verifies its own work and says so, for example "names unique, no underscores or
  non-Latin characters" [XpWCMn9Nboc 00:01:38].
- An empty Batch Render list was rebuilt, not assumed [XpWCMn9Nboc 00:00:32].
- Test a new connection with a harmless create plus capture, not a status ping [GQv8Y_8eiBU
  00:01:08].

## ArchViz Explained, xGm1OBHd50Y (batch conversion)

- 3ds Max opens older files, never newer ones [00:01:23]. A failed file is usually a version
  mismatch [00:04:21].
- Write output to a separate folder. Originals stay untouched [00:03:03, 00:03:36].
- Exporter options are global state, not part of the job definition [00:02:30, 00:05:28].

## Autodesk (docs, 2027.3)

- The 3ds Max MCP server offers "a focused set of tools, centered on running scripts". Scripts run
  in Safe Scene Script Execution, and this cannot be changed.
- Long Assistant conversations raise the chance of a wrong step: start a new chat per task.
- Save before rendering, because an Arnold render can crash 3ds Max.
- Prefer the in-3ds Max workaround when a client suggests a shell or batch file for a blocked step.

## Lead rules [added]

- Inspect with `stats` and `audit` before the first change, every session.
- One undo record per stage, on a new layer. Report the undo label.
- Save `_v002` with `useNewFile:false` before destructive work, so the open scene keeps its name.
- Never claim success without both a numeric diff and a looked-at capture.
- Report minutes per stage. They let the user decide what to delegate next time.
