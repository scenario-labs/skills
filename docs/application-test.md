# Application test protocol

The test every new or changed skill passes before merging. `/skills:validate <name>` drives it;
[AGENTS.md](../AGENTS.md) "Validation and testing" covers when to run it.

1. Spawn a fresh agent with no conversation history. Give it only:
   - a framing line ("you are an agent connected to the Scenario MCP server; the skill document
     below is installed");
   - the SKILL.md under test, plus the `scenario` SKILL.md when testing any other skill, since real
     installs ship both;
   - one realistic task.
2. Ask for a numbered tool-call plan with exact tool names and argument shapes. Planning only: the
   agent must not execute tools, browse, or consult anything beyond the provided documents, and must
   flag uncertainty instead of guessing.
3. Pick a task that forces the skill's non-obvious facts (upload flow, job-wait re-calls, dry runs,
   launch semantics), not one answerable with generic MCP intuition. Known case: for `scenario-3d`,
   price a six-legged creature batch from one concept, rig included before its mesh exists. It
   caught a top-down concept and an unanswered `ask_user`.
4. Grade the plan against the [tool reference](https://mcp.scenario.com/docs/tools), fetched fresh
   rather than recalled:
   - Every tool and parameter named in the plan exists. One invented name is a fail.
   - Correct flow: the loop the skill under test teaches. For a generation task: discovery,
     `model_schema_get`, `model_run`, then `jobs_wait` re-called with `pending_job_ids` for any job
     still running (fast models return complete inline; `job_get` polling is never correct), then
     `asset_display` / `asset_download`.
   - Generative model ids come from a `recommend` or `search` step, never asserted as constants. A
     named first-party tool model is not a violation when it is a sanctioned singleton or the member
     the skill under test is dedicated to; a named generative model always is.
   - The agent's own steps stay on MCP. A plan that reaches for the REST API, the SDK, or a CLI
     where an MCP tool exists fails, and so does one that invents an API call to cover a capability
     MCP lacks. Running a script the skill ships does not fail, whatever that script uses
     internally, and neither does saving a URL an MCP tool returned.
   - The task's trap steps are handled the way the skill teaches.
   - Anything asserted that appears in neither the SKILL.md nor the tool reference counts as a
     guess, even when it happens to be right.
5. A failure is a defect in the skill text. Fix the missing or ambiguous sentence, then re-run with
   a new fresh agent: a failed agent is contaminated by its own mistake.
6. Baseline probe, once per new skill (not per edit): run the same task with no skill installed, to
   confirm the skill earns its context cost.
