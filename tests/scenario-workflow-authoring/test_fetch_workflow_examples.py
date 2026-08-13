"""fetch_workflow_examples: auth, pagination, tag filtering, trimming. No network."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock as mock
import urllib.parse
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "scenario-workflow-authoring" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import fetch_workflow_examples as fwe

ENV = {"SCENARIO_API_KEY": "key", "SCENARIO_API_SECRET": "secret"}


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def serve_pages(pages: list[dict], requests: list, details: dict | None = None) -> mock.Mock:
    """urlopen stand-in: replays canned list pages, routes /workflows/{id} to details."""
    detail_payloads = details or {}

    def _open(request, timeout=None):
        requests.append(request)
        path = urllib.parse.urlparse(request.full_url).path
        if not path.endswith("/workflows"):
            wid = urllib.parse.unquote(path.rsplit("/", 1)[-1])
            return FakeResponse(detail_payloads[wid])
        served = sum(
            1 for r in requests if urllib.parse.urlparse(r.full_url).path.endswith("/workflows")
        )
        return FakeResponse(pages[min(served, len(pages)) - 1])

    return mock.Mock(side_effect=_open)


def graph_workflow(wid: str, tags: list[str] | None, **overrides) -> dict:
    workflow = {
        "id": wid,
        "name": f"Workflow {wid}",
        "description": "desc",
        "tagSet": tags,
        "inputs": {"prompt": {"type": "text"}},
        "editorInfo": {
            "nodes": [{"id": "n1", "type": "model", "data": {"modelId": "m"}}],
            "edges": [],
        },
    }
    if tags is None:
        del workflow["tagSet"]
    workflow.update(overrides)
    return workflow


def run_main(pages: list[dict], argv: list[str], env: dict | None = ENV, details: dict | None = None):
    requests: list = []
    out, err = io.StringIO(), io.StringIO()
    environ = dict(env) if env else {}
    with mock.patch("urllib.request.urlopen", serve_pages(pages, requests, details)) as opener:
        with mock.patch.dict(os.environ, environ, clear=True):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = fwe.main(argv)
    return code, requests, out.getvalue(), err.getvalue(), opener


def query_of(request) -> dict:
    return urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)


class AuthTestCase(unittest.TestCase):
    def test_header_is_basic_base64_of_key_colon_secret(self) -> None:
        # base64("key:secret") == "a2V5OnNlY3JldA=="
        self.assertEqual(fwe.build_auth_header("key", "secret"), "Basic a2V5OnNlY3JldA==")

    def test_requests_carry_the_auth_header(self) -> None:
        _, requests, _, _, _ = run_main([{"workflows": []}], [])
        self.assertEqual(requests[0].get_header("Authorization"), "Basic a2V5OnNlY3JldA==")

    def test_missing_env_vars_fail_before_any_request(self) -> None:
        code, requests, _, err, opener = run_main([{"workflows": []}], [], env=None)
        self.assertEqual(code, 1)
        self.assertIn("SCENARIO_API_KEY", err)
        self.assertIn("SCENARIO_API_SECRET", err)
        self.assertEqual(requests, [])
        opener.assert_not_called()


class PaginationTestCase(unittest.TestCase):
    def test_first_request_asks_for_public_workflows(self) -> None:
        _, requests, _, _, _ = run_main([{"workflows": []}], [])
        query = query_of(requests[0])
        self.assertEqual(query["privacy"], ["public"])
        self.assertEqual(query["pageSize"], [str(fwe.PAGE_SIZE)])
        self.assertNotIn("paginationToken", query)

    def test_follows_next_pagination_token_until_exhausted(self) -> None:
        pages = [
            {"workflows": [], "nextPaginationToken": "tok-1"},
            {"workflows": [], "nextPaginationToken": "tok-2"},
            {"workflows": []},
        ]
        code, requests, _, _, _ = run_main(pages, [])
        self.assertEqual(code, 0)
        self.assertEqual(len(requests), 3)
        self.assertEqual(query_of(requests[1])["paginationToken"], ["tok-1"])
        self.assertEqual(query_of(requests[2])["paginationToken"], ["tok-2"])

    def test_max_pages_caps_the_walk(self) -> None:
        endless = [{"workflows": [], "nextPaginationToken": "again"}] * 10
        _, requests, _, _, _ = run_main(endless, ["--max-pages", "2"])
        self.assertEqual(len(requests), 2)


class TagFilterTestCase(unittest.TestCase):
    def run_filter(self, workflows: list[dict], argv: list[str] | None = None):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, out, err, _ = run_main(
                [{"workflows": workflows}], ["--output-dir", tmp, *(argv or [])]
            )
            written = sorted(p.stem for p in Path(tmp).glob("*.json"))
        return code, written, out, err

    def test_keeps_featured_and_sc_featured_only(self) -> None:
        code, written, _, _ = self.run_filter(
            [
                graph_workflow("a", ["featured"]),
                graph_workflow("b", ["sc:featured", "tool"]),
                graph_workflow("c", ["upscale"]),
                graph_workflow("d", None),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(written, ["a", "b"])

    def test_tag_flag_overrides_the_default_set(self) -> None:
        code, written, _, _ = self.run_filter(
            [graph_workflow("a", ["featured"]), graph_workflow("b", ["mine"])],
            ["--tag", "mine"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(written, ["b"])

    def test_tagged_workflow_without_editor_graph_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, requests, _, err, _ = run_main(
                [
                    {
                        "workflows": [
                            graph_workflow("a", ["featured"], editorInfo={"nodes": [], "edges": []}),
                            graph_workflow("b", ["featured"], editorInfo=None),
                        ]
                    }
                ],
                ["--output-dir", tmp],
                details={
                    "a": {"workflow": {"id": "a", "name": "Workflow a"}},
                    "b": {"workflow": {"id": "b", "name": "Workflow b"}},
                },
            )
            written = sorted(p.stem for p in Path(tmp).glob("*.json"))
        self.assertEqual(code, 0)
        self.assertEqual(written, [])
        self.assertIn("no editor graph", err)
        # The full record was consulted before each skip.
        detail_paths = [
            urllib.parse.urlparse(r.full_url).path
            for r in requests
            if not urllib.parse.urlparse(r.full_url).path.endswith("/workflows")
        ]
        self.assertEqual(detail_paths, ["/v1/workflows/a", "/v1/workflows/b"])

    def test_listing_without_graph_falls_back_to_the_full_record(self) -> None:
        listed = graph_workflow("a", ["featured"])
        del listed["editorInfo"]
        detail = {"workflow": graph_workflow("a", ["featured"])}
        with tempfile.TemporaryDirectory() as tmp:
            code, requests, out, _, _ = run_main(
                [{"workflows": [listed]}], ["--output-dir", tmp], details={"a": detail}
            )
            payload = json.loads((Path(tmp) / "a.json").read_text())
        self.assertEqual(code, 0)
        self.assertEqual(payload["nodes"], [{"id": "n1", "type": "model", "data": {"modelId": "m"}}])
        self.assertIn("Wrote 1", out)
        self.assertEqual(len(requests), 2)

    def test_zero_matches_still_exits_zero_with_a_notice(self) -> None:
        code, written, out, _ = self.run_filter([graph_workflow("c", ["upscale"])])
        self.assertEqual(code, 0)
        self.assertEqual(written, [])
        self.assertIn("No public workflows", out)
        self.assertIn("Wrote 0", out)


class TrimTestCase(unittest.TestCase):
    def test_node_data_keeps_the_allowlist_and_drops_content(self) -> None:
        workflow = graph_workflow(
            "w",
            ["featured"],
            editorInfo={
                "nodes": [
                    {
                        "id": "n1",
                        "type": "model",
                        "position": {"x": 1, "y": 2},
                        "width": 300,
                        "height": 200,
                        "data": {
                            "type": "image-generation",
                            "modelId": "model-123",
                            "title": "Generate",
                            "isInput": True,
                            "isOutput": False,
                            "prompt": "a castle at dawn",
                            "assetId": "asset-999",
                            "imageUrl": "https://example.com/x.png",
                        },
                    },
                    {"id": "n2", "type": "output", "data": {"assetId": "asset-1"}},
                ],
                "edges": [
                    {
                        "id": "e1",
                        "type": "smooth",
                        "source": "n1",
                        "sourceHandle": "image",
                        "target": "n2",
                        "targetHandle": "input",
                        "data": {"color": "red"},
                    }
                ],
            },
        )
        trimmed = fwe.trim_workflow(workflow)
        self.assertEqual(
            trimmed["nodes"][0],
            {
                "id": "n1",
                "type": "model",
                "data": {
                    "type": "image-generation",
                    "modelId": "model-123",
                    "title": "Generate",
                    "isInput": True,
                    "isOutput": False,
                },
            },
        )
        self.assertNotIn("position", trimmed["nodes"][0])
        # A node whose data is all content ends up with no data key at all.
        self.assertEqual(trimmed["nodes"][1], {"id": "n2", "type": "output"})
        self.assertEqual(
            trimmed["edges"],
            [{"source": "n1", "sourceHandle": "image", "target": "n2", "targetHandle": "input"}],
        )

    def test_false_is_kept_but_none_is_dropped(self) -> None:
        node = fwe.trim_node({"id": "n", "type": "t", "data": {"isOutput": False, "modelId": None}})
        self.assertEqual(node["data"], {"isOutput": False})

    def test_output_file_has_only_the_contract_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _, _, _ = run_main(
                [{"workflows": [graph_workflow("w1", ["featured"])]}], ["--output-dir", tmp]
            )
            self.assertEqual(code, 0)
            payload = json.loads((Path(tmp) / "w1.json").read_text())
        self.assertEqual(
            set(payload), {"id", "name", "description", "nodes", "edges", "inputKeys"}
        )
        self.assertEqual(payload["id"], "w1")
        self.assertEqual(payload["inputKeys"], ["prompt"])

    def test_input_keys_from_dict_list_and_absent_inputs(self) -> None:
        self.assertEqual(fwe.input_keys({"inputs": {"a": {}, "b": {}}}), ["a", "b"])
        self.assertEqual(
            fwe.input_keys({"inputs": [{"key": "x"}, {"name": "y"}, "z", {"other": 1}]}),
            ["x", "y", "z"],
        )
        self.assertEqual(fwe.input_keys({"inputKeys": ["k1", "k2"]}), ["k1", "k2"])
        self.assertEqual(fwe.input_keys({}), [])

    def test_editor_info_input_keys_win_over_fallbacks(self) -> None:
        # Live records keep the ordered pin list at editorInfo.inputKeys.
        workflow = {
            "editorInfo": {"inputKeys": ["text1", "image5"]},
            "inputKeys": ["stale"],
            "inputs": {"other": {}},
        }
        self.assertEqual(fwe.input_keys(workflow), ["text1", "image5"])
        # An empty editorInfo list still defers to the fallbacks.
        self.assertEqual(
            fwe.input_keys({"editorInfo": {"inputKeys": []}, "inputs": {"a": {}}}), ["a"]
        )

    def test_for_each_end_keeps_its_parent_node_id(self) -> None:
        node = fwe.trim_node(
            {"id": "fe1_end", "type": "forEachEnd", "data": {"parentNodeId": "fe1"}}
        )
        self.assertEqual(node, {"id": "fe1_end", "type": "forEachEnd", "data": {"parentNodeId": "fe1"}})

    def test_workflow_without_nodes_is_not_an_example(self) -> None:
        self.assertIsNone(fwe.trim_workflow({"id": "w", "editorInfo": {"edges": []}}))
        self.assertIsNone(fwe.trim_workflow({"id": "w"}))


class HttpErrorTestCase(unittest.TestCase):
    def test_http_401_becomes_a_readable_credentials_error(self) -> None:
        import urllib.error

        def _raise(request, timeout=None):
            raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", None, None)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch("urllib.request.urlopen", side_effect=_raise):
            with mock.patch.dict(os.environ, ENV, clear=True):
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = fwe.main([])
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", err.getvalue())
        self.assertIn("SCENARIO_API_KEY", err.getvalue())


if __name__ == "__main__":
    unittest.main()
