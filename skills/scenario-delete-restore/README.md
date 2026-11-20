# scenario-delete-restore: build notes

Maintainer notes, not runtime instructions. SKILL.md does not link this file.

## Why a skill of its own

- No skill mentions deleting or restoring assets, models, or collections.
- MCP server 0.40.0 (2026-11-13) added `asset_restore`, `model_restore`, `assets_list`
  `deleted: true`, and `models_list` `filters.status: "deleted"`.
- The `scenario` body sits at the 2500-word cap, and `scenario-team-admin` is an admin skill whose
  description is near its 500-character limit. Neither triggers on "bring back what I deleted". A
  dedicated description does.

## Where each fact comes from

- Tool pages at mcp.scenario.com/docs/tools: `asset-restore`, `model-restore`, `assets-list`,
  `asset-delete`, `model-delete`, `collection-delete`, and the live `scenario_tools_search` schemas.
  - The plan list (Max, Team, legacy Premium, Enterprise) and the `skipped` reasons are quoted from
    `asset_restore`.
  - `model_restore` documents the refusals without status codes, so the skill names none.
- The two refused pairs (`filters` with `deleted: true`, `privacy: "public"` with
  `status: "deleted"`) were confirmed with read-only calls on 2026-11-15; each error names the fix.
- The 100-id cap on `asset_delete` comes from the server's own error text. The schema carries no
  `maxItems`, so re-check it if the server changes.
- `collectionIds` and `tags` on `assets_list` rows: a read-only listing on 2026-11-15.
- No restore tool exists for collections: `scenario_tools_search` for "restore undelete" returns
  only `asset_restore` and `model_restore`.
