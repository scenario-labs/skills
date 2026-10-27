"""
agent_python_toolset: a project-local MCP toolset that runs Python in the open editor.

STATUS: run in Unreal Engine 5.8.3 (macOS, headless editor) on 2026-10-21: registered as
`agent.AgentPythonToolset`, listed by Epic's list_toolsets, `run_python` executed code with the
unreal module, kept variables between calls, returned print output and `result`, and raised a
traceback on error. Not tried: 5.6 and 5.7 (no Toolset Registry there), Windows, Linux.

Why: Epic's 5.8 toolsets cover many edits but none executes editor Python (execute_tool_script is a
sandbox without the unreal module), and Python Remote Execution needs a project setting, a matching
multicast bind address (0.0.0.0 on macOS and Linux, which opens the editor to the local network) and
a client that speaks Epic's UDP discovery protocol. This toolset runs behind the MCP connection the
agent already has, with no multicast.

Opt-in and unsafe by design: it runs any code with full editor access, and Epic's MCP endpoint has
no authentication (loopback only). Install in throwaway or trusted projects, never on a machine
whose loopback ports other users can reach. Install with `ue_env.install_python_toolset(project)`
or by hand: copy this file to <project>/Content/Python/ and add to <project>/Content/Python/init_unreal.py

    import agent_python_toolset
    agent_python_toolset.register()

then restart the editor (init_unreal.py runs at startup; a running editor does not pick it up).
Call: call_tool(toolset_name="agent.AgentPythonToolset", tool_name="run_python", arguments={"code": ...}).
The `agent.` prefix comes from this file's name, not the class: keep the file name, or every call
and ue_env.install_python_toolset must change with it.
"""

__version__ = "0.2.1"
import contextlib
import io
import traceback

import unreal
import toolset_registry  # only inside the editor, like unreal

_NS = {"unreal": unreal, "__name__": "agent_python"}


@unreal.uclass()
class AgentPythonToolset(unreal.ToolsetDefinition):
    """Runs Python code inside the open editor, where the unreal module has the full editor API.
    State persists between calls (variables, imports)."""

    @toolset_registry.tool_call
    @staticmethod
    def run_python(code: str) -> str:
        """Executes Python in the editor's interpreter on the game thread.

        Args:
            code: Python source. Print to return text; assign `result` to return a value (str() of it).

        Returns:
            Everything printed, then `result=<value>` if result was set. Raises with the traceback on error.
        """
        buf = io.StringIO()
        _NS.pop("result", None)
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                exec(compile(code, "<agent>", "exec"), _NS)
        except Exception:
            raise RuntimeError(buf.getvalue() + traceback.format_exc())
        out = buf.getvalue()
        if "result" in _NS:
            out += ("\n" if out and not out.endswith("\n") else "") + "result=" + str(_NS["result"])
        return out


def register():
    unreal.ToolsetRegistry.register_toolset_class(AgentPythonToolset)
