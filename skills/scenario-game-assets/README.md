# Maintaining the isometric references

The template builder produces neutral geometry independently of generative model availability. Tests cover shared neighbor edges, disjoint ground/side regions, vertical editing space, and reproducible output. The PNGs are build artifacts; the source geometry and manifest describe their placement.

## Publication, Scenarians only

Publishing shared reference assets requires staff access. Supply the destination team and project at runtime; do not embed their names, IDs, credentials, or private asset records in this repository.

1. Build and inspect the contact sheet. Test a small assembled map before publishing a version as validated.
2. Resolve the supplied scope with `teams_list` and `projects_list`. Upload the reference and region PNGs with `upload_asset`, following its returned instructions and `upload_asset_complete` when required.
3. Use catalog `asset_add_tags` for `skill:scenario-game-assets:isometric`, the template name, and the role. Create a named collection with `collection_create`, then file assets with `collection_add_assets`. Catalog executor inputs go under `parameters`.
4. Publish using the supported staff surface. The documented MCP `asset_update` exposes name, description, and tags, not publication. Do not invent a visibility field or equate a destination team's name with public access. If publication is unavailable, retain the IDs privately and report the gap.
5. Verify access from a scope outside the owning team, including download and reference use. Only then add an `asset_id` to each file entry in `isometric-templates.json`, reusing an ID where files are identical. Keep the guide procedural; asset records belong in JSON. Never put signed download URLs or destination IDs there.

Published versions are immutable references. A geometry change gets a new version and a new validation; keep old assets available while skills still reference them. A staff-only publication procedure does not restrict ordinary users from consuming the public templates or building local copies.
