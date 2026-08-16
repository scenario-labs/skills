# Where references actually come from

## Rule zero

A reference informs a prompt. It never ships. Do not reproduce one compositionally, do not drop one into the deliverable as a placeholder to swap later, and never cite a reference you did not actually look at. Take one named mechanic per reference ("pinned silhouette, detail scrolls past it"), not "the vibe".

Describing a living artist's style by name in a prompt is both a rights risk and a moderation risk (see `scenario-moderation`). Name the attributes instead: line weight, palette relationship, edge treatment, value structure. The attributes are what you wanted anyway, and they survive a model switch.

## Lane 1: the team's own assets

The most skipped lane, and usually the best one, because it is already on brand and already licensed. `search` with `target: "assets"` and `public` omitted searches the current project. Run it at both ends of `query_semantic_ratio`: keyword matches the asset's stored caption text, so 0.8 is what finds a concept the caption never spelled out.

Existing collections are prior art. `collections_list`, then `search` with `filters.collection_ids`, tells you what direction this team already chose once.

## Lane 2: the Scenario public catalog

`search` with `public: true` reaches assets published by other teams, and it carries two things a normal image search does not.

- Asset hits include `metadata.prompt`, the wording that produced the image. Read it. A prompt is a better souvenir than a JPEG, because it transfers.
- Model hits (`target: "models"`) include `shortDescription`, `tags`, and `exampleAssetIds`. A style model's examples are a finished board for that look, free to browse with `asset_display`, and the model itself is then runnable.

A public asset stays owned by its team. Display it, seed searches with it, read its prompt; to put it on your board you need your own copy (see [moodboard.md](moodboard.md)).

## Lane 3: the open web

| Source                   | Reachable                          | Key | Notes                                                                                                                   |
| ------------------------ | ---------------------------------- | --- | ----------------------------------------------------------------------------------------------------------------------- |
| Pinterest                | No, see below                      | n/a | `robots.txt` ends `User-agent: *` / `Disallow: /`                                                                       |
| Are.na                   | Yes, `api.are.na/v2`               | No  | `/channels/<slug>/contents?per=N`; blocks carry `image.display.url`                                                     |
| The Met                  | Yes, `collectionapi.metmuseum.org` | No  | `/public/collection/v1/search?q=&hasImages=true`, then `/objects/<id>`; check `isPublicDomain`, download `primaryImage` |
| Openverse                | Yes, `api.openverse.org/v1`        | No  | Returns `license` and `attribution`; filter them, several forbid derivatives                                            |
| Wikimedia Commons        | Yes, rate limited                  | No  | Send a descriptive User-Agent and back off on 429                                                                       |
| Art Institute of Chicago | API yes, images unreliable         | No  | `api.artic.edu/api/v1/artworks/search`; its image host may refuse a fetch                                               |

Are.na is the closest legitimate equivalent to a public moodboard service: channels are user-curated reference collections, and the API serves them without a key.

Text search often beats image search here. Learning that a look is called a specific movement, or that a technique has a name, gives you a query seed that works in every other lane. An image you cannot name is hard to search with; a name is not.

**Pinterest.** Its `robots.txt` allowlists named crawlers by name and closes with `User-agent: *` / `Disallow: /`, so an agent is disallowed from the whole site. Do not fetch it, do not scrape it, and do not route around it with a third-party mirror. Say so plainly and offer the route that works: ask the user to open the board themselves and hand over the images (a board's own download, or specific files they have the right to use). Their board is still the best input in this document; it just arrives through them.

## Lane 4: the user

Ask for three things they already love and one they cannot stand, in any medium. This is the highest-yield lane and the cheapest. It also fixes two known problems at once: a user who supplies the divergent seed keeps ownership of the result, and two teams briefing the same agent stop receiving the same answer.

When they name something you cannot see, do not guess. Ask for the file, the URL, or the exact title.

## Bringing an outside image in

Anything from lanes 3 and 4 has to become an asset in your project before it can be boarded or used as a reference:

1. Save the file locally (`curl -L` follows the redirects these hosts use).
2. `upload_asset` with `file_name`, `content_type`, `kind: "image"`, and `file_size`, then PUT each returned part URL and call `upload_asset_complete`. Inline `data` is for files under about 100KB only.
3. `collection_add_assets` in chunks of at most 49 ids.
4. `asset_update` the description with why it is on the board, and `asset_add_tags` its role.

Keep the source URL in the description. A board whose references cannot be traced back is unusable the moment someone asks where an image came from.
