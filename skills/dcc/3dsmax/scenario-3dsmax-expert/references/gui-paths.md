# GUI paths (for a human or a computer-use agent)

Menu paths are from the 2027.3 docs unless marked otherwise. Layouts vary with workspaces: search
the menu by name if a path differs.

| Task                                      | Path                                                                                                                                                                                                 |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Turn on the Autodesk 3ds Max MCP server   | Customize > Preferences > MCP tab > enable "3ds Max MCP Server" > set "MCP tools enabled" > Authentication: "New token on demand" > OK                                                               |
| Copy the client entry                     | Customize > Preferences > MCP tab > Copy next to "mcp.json entry" (one per running instance)                                                                                                         |
| Change the tool level                     | same tab; then reload the server in the client                                                                                                                                                       |
| Run a handoff script                      | Scripting > Run Script > pick the .ms or .py file                                                                                                                                                    |
| Read script output                        | Scripting > MAXScript Listener (F11)                                                                                                                                                                 |
| Save a copy without renaming the scene    | File > Save As > Save Copy As (path not re-confirmed for 2027.3)                                                                                                                                     |
| Units                                     | Customize > Units Setup > System Unit Setup (2017 help path; Enhanced menu: Customize > Customization > Units Setup); 2027.1: Customize > Preferences > Files for unit rules on load, merge and XRef |
| Missing maps                              | Asset Tracking dialog: repath and locate missing files (menu path not in the saved 2027 page)                                                                                                        |
| Safe Frame in a viewport                  | Shift+F, or viewport label menu                                                                                                                                                                      |
| Batch render list                         | Rendering > Batch Render (set the view camera here, not by script: reading it by script crashes 3ds Max)                                                                                             |
| Render Setup                              | Rendering > Render Setup (F10)                                                                                                                                                                       |
| Bake to Texture                           | Rendering > Bake to Texture (hotkey 0)                                                                                                                                                               |
| Import glTF (2027.3)                      | File > Import > "glTF 2.0 (KHRglTFImporter_adsk)"                                                                                                                                                    |
| Export glTF (2027.3)                      | File > Export > "GL Transmission Format"                                                                                                                                                             |
| Scene Explorer and layers                 | Scene Explorer (menu path not in the saved page)                                                                                                                                                     |
| Startup scripts the MCP server cannot add | save the script in the user `scripts\startup` folder, then restart 3ds Max                                                                                                                           |
| Admin MCP level                           | registry `HKEY_LOCAL_MACHINE\SOFTWARE\Autodesk\3ds Max 2027`, value `ADSK_3DSMAX_MCP_LEVEL` (REG_DWORD); or an environment variable of the same name; read at startup                                |
| Autodesk Assistant                        | in-app Assistant panel; MCP server tools and "Trusted scripting" set in its preferences                                                                                                              |

## GUI-only work an agent should hand back

- Closing a dialog a script opened (mcp-safe).
- Setting exporter or plugin options stored in INI files (mcp-safe).
- Hotkeys (Hotkey Editor).
- Biped footstep scaling and retiming (Biped UI). These crash 3ds Max when called through MCP.
- Composition, planting and lighting taste calls. Agents produce a first pass, and the artist
  refines it.
