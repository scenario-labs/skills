#!/usr/bin/env python3
"""Fetch public featured Scenario workflows as structural wiring examples.

Lists public workflows from the Scenario REST API, keeps the ones tagged
featured (or sc:featured) that carry an editor graph, and writes one trimmed
JSON file per workflow. The trim keeps node types, edge wiring, and input
keys, and drops content values (prompts, asset ids, parameter values): each
file is a structural reference for wiring a similar workflow, never content
to reuse.

    SCENARIO_API_KEY=... SCENARIO_API_SECRET=... \\
        python3 scripts/fetch_workflow_examples.py --output-dir workflow-examples

API surface per the Workflows & Apps page on https://docs.scenario.com:
GET https://api.cloud.scenario.com/v1/workflows with HTTP Basic auth
(base64 of key:secret), privacy=public to list public workflows, pageSize
(max 100) plus paginationToken for paging, and a nextPaginationToken field
in the response for the next page.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.cloud.scenario.com/v1/workflows"

# Documented maximum page size (default is 50).
PAGE_SIZE = 100

DEFAULT_TAGS = ("featured", "sc:featured")

# Structural node data worth keeping. Everything else in a node's data is
# content (prompt text, asset references, parameter values) and is dropped.
NODE_DATA_KEYS = ("type", "modelId", "title", "isInput", "isOutput")

EDGE_KEYS = ("source", "sourceHandle", "target", "targetHandle")


def build_auth_header(key: str, secret: str) -> str:
    token = base64.b64encode(f"{key}:{secret}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def fetch_page(auth_header: str, pagination_token: str | None = None, page_size: int = PAGE_SIZE) -> dict:
    params = {"privacy": "public", "pageSize": str(page_size)}
    if pagination_token:
        params["paginationToken"] = pagination_token
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": auth_header, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        hint = " (check SCENARIO_API_KEY / SCENARIO_API_SECRET)" if err.code in (401, 403) else ""
        raise RuntimeError(f"GET {API_URL} failed with HTTP {err.code}{hint}") from err
    except urllib.error.URLError as err:
        raise RuntimeError(f"GET {API_URL} failed: {err.reason}") from err


def iter_public_workflows(auth_header: str, max_pages: int, page_size: int = PAGE_SIZE):
    token = None
    for _ in range(max_pages):
        page = fetch_page(auth_header, token, page_size)
        yield from page.get("workflows") or []
        token = page.get("nextPaginationToken")
        if not token:
            break


def _pick(source: dict, keys: tuple[str, ...]) -> dict:
    return {key: source[key] for key in keys if source.get(key) is not None}


def trim_node(node: dict) -> dict:
    trimmed = _pick(node, ("id", "type"))
    data = node.get("data")
    if isinstance(data, dict):
        kept = _pick(data, NODE_DATA_KEYS)
        if kept:
            trimmed["data"] = kept
    return trimmed


def trim_edge(edge: dict) -> dict:
    return _pick(edge, EDGE_KEYS)


def input_keys(workflow: dict) -> list[str]:
    keys = workflow.get("inputKeys")
    if isinstance(keys, list) and all(isinstance(k, str) for k in keys):
        return keys
    # The docs show an inputs field on workflow objects without pinning its
    # shape, so accept the likely shapes and fall back to an empty list.
    inputs = workflow.get("inputs")
    if isinstance(inputs, dict):
        return list(inputs.keys())
    if isinstance(inputs, list):
        found = []
        for item in inputs:
            if isinstance(item, str):
                found.append(item)
            elif isinstance(item, dict):
                for field in ("key", "name", "id"):
                    value = item.get(field)
                    if isinstance(value, str):
                        found.append(value)
                        break
        return found
    return []


def trim_workflow(workflow: dict) -> dict | None:
    """Trim a workflow to its structural wiring, or None without an editor graph."""
    editor_info = workflow.get("editorInfo")
    if not isinstance(editor_info, dict):
        return None
    nodes = editor_info.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return None
    edges = editor_info.get("edges")
    if not isinstance(edges, list):
        edges = []
    return {
        "id": workflow.get("id"),
        "name": workflow.get("name") or "",
        "description": workflow.get("description") or "",
        "nodes": [trim_node(node) for node in nodes if isinstance(node, dict)],
        "edges": [trim_edge(edge) for edge in edges if isinstance(edge, dict)],
        "inputKeys": input_keys(workflow),
    }


def write_example(output_dir: str, trimmed: dict) -> str:
    os.makedirs(output_dir, exist_ok=True)
    # Defensive: an id must never escape the output directory.
    safe_id = str(trimmed["id"]).replace("/", "_").replace("\\", "_")
    path = os.path.join(output_dir, f"{safe_id}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(trimmed, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", default="./workflow-examples", help="where the trimmed JSON files go")
    parser.add_argument("--max-pages", type=int, default=5, help="page cap for the listing (default 5)")
    parser.add_argument(
        "--tag",
        action="append",
        help="tag to keep, repeatable (default: featured and sc:featured)",
    )
    args = parser.parse_args(argv)
    if args.max_pages < 1:
        parser.error("--max-pages must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    key = os.environ.get("SCENARIO_API_KEY", "").strip()
    secret = os.environ.get("SCENARIO_API_SECRET", "").strip()
    if not key or not secret:
        print(
            "SCENARIO_API_KEY and SCENARIO_API_SECRET must be set: the workflows"
            " endpoint requires HTTP Basic auth with your Scenario API key and secret.",
            file=sys.stderr,
        )
        return 1

    auth_header = build_auth_header(key, secret)
    wanted = set(args.tag) if args.tag else set(DEFAULT_TAGS)
    kept = 0
    try:
        for workflow in iter_public_workflows(auth_header, args.max_pages):
            # Tag filtering happens client side: the documented tags query
            # parameter does not state how multiple tags combine, and this
            # needs any-of semantics.
            if not set(workflow.get("tagSet") or []) & wanted:
                continue
            if not workflow.get("id"):
                print("skipping a tagged workflow with no id", file=sys.stderr)
                continue
            trimmed = trim_workflow(workflow)
            if trimmed is None:
                print(f"skipping {workflow['id']}: tagged but has no editor graph", file=sys.stderr)
                continue
            path = write_example(args.output_dir, trimmed)
            kept += 1
            print(
                f"{trimmed['id']}: {trimmed['name']}"
                f" ({len(trimmed['nodes'])} nodes, {len(trimmed['edges'])} edges,"
                f" {len(trimmed['inputKeys'])} inputs) -> {path}"
            )
    except RuntimeError as err:
        print(str(err), file=sys.stderr)
        return 1

    if kept == 0:
        print(f"No public workflows tagged {sorted(wanted)} with an editor graph were found.")
    print(f"Wrote {kept} workflow example(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
