"""Run each component's function against a mocked SDK that returns real anakin models.

`autospec` makes a call with a wrong argument name fail, as the real SDK would.
"""

import json
from unittest import mock

import httpx
import pytest
from anakin import Anakin
from anakin.client import (
    AIVisibilityResource,
    MonitorsResource,
    SessionsResource,
    WireResource,
)
from anakin.models import (
    AgenticSearchResult,
    AIVisibilitySearch,
    AIVisibilitySource,
    CrawlResult,
    Document,
    MapResult,
    Monitor,
    MonitorChange,
    MonitorRun,
    SearchResult,
    WireActionMatch,
    WireLoginResult,
    WireResult,
)
from kfp import dsl

import kfp_anakin
from kfp_anakin._helpers import redact_webhook_secret, refuse_if_financial


@pytest.fixture
def client():
    instance = mock.create_autospec(Anakin, instance=True, spec_set=False)
    instance.wire = mock.create_autospec(WireResource, instance=True)
    instance.monitors = mock.create_autospec(MonitorsResource, instance=True)
    instance.ai_visibility = mock.create_autospec(AIVisibilityResource, instance=True)
    instance.sessions = mock.create_autospec(SessionsResource, instance=True)
    with mock.patch("anakin.Anakin", return_value=instance):
        yield instance


@pytest.fixture
def dataset(tmp_path):
    artifact = dsl.Dataset(name="out")
    artifact.path = str(tmp_path / "out.jsonl")
    return artifact


def rows(artifact):
    with open(artifact.path, encoding="utf-8") as lines:
        return [json.loads(line) for line in lines]


def call(name, **kwargs):
    return getattr(kfp_anakin, name).python_func(**kwargs)


def test_scrape_writes_the_document(client, dataset) -> None:
    client.scrape.return_value = Document(
        id="job1", url="https://a.io", status="completed", markdown="# héllo", cached=True
    )
    call("scrape_url", document=dataset, url="https://a.io", country="de", use_browser=True)

    client.scrape.assert_called_once_with(
        "https://a.io",
        formats=("markdown",),
        country="de",
        use_browser=True,
        generate_json=False,
        output_schema=None,
        force_fresh=False,
        session_id=None,
        session_name=None,
        poll_timeout=None,
    )
    assert rows(dataset)[0]["markdown"] == "# héllo"
    assert dataset.metadata == {"rows": 1, "job_id": "job1", "status": "completed", "cached": True}


def test_map_returns_urls_for_parallel_for(client) -> None:
    client.map.return_value = MapResult(
        id="m",
        links=["https://a.io/1", "https://a.io/2"],
        totalLinks=2,
        externalLinks=["https://b.io"],
    )
    result = call("map_site", url="https://a.io")
    assert result.urls == ["https://a.io/1", "https://a.io/2"]
    assert result.total_links == 2
    assert result.external_urls == ["https://b.io"]


def test_crawl_writes_one_row_per_page(client, dataset) -> None:
    client.crawl.return_value = CrawlResult(
        id="c",
        totalPages=2,
        completedPages=1,
        results=[
            {"url": "https://a.io/1", "status": "completed", "markdown": "one"},
            {"url": "https://a.io/2", "status": "failed", "error": "boom"},
        ],
    )
    call("crawl_site", pages=dataset, url="https://a.io", include_patterns=["/docs/*"])
    assert client.crawl.call_args.kwargs["include_patterns"] == ["/docs/*"]
    assert client.crawl.call_args.kwargs["exclude_patterns"] == ()
    assert [r["status"] for r in rows(dataset)] == ["completed", "failed"]
    assert dataset.metadata["rows"] == 2
    assert dataset.metadata["completed_pages"] == 1


def test_search_returns_urls_and_results(client) -> None:
    client.search.return_value = SearchResult(
        id="s", results=[{"url": "https://a.io", "title": "A"}]
    )
    result = call("search", prompt="q", limit=1)
    client.search.assert_called_once_with("q", limit=1)
    assert result.urls == ["https://a.io"]
    assert result.results[0]["title"] == "A"
    json.dumps(result.results)


def test_agentic_search_writes_the_answer(client, dataset) -> None:
    client.agentic_search.return_value = AgenticSearchResult(
        id="r", status="completed", generatedJson={"summary": "s"}
    )
    call("agentic_search", result=dataset, prompt="q", schema={"type": "object"})
    client.agentic_search.assert_called_once_with(
        "q", use_browser=True, schema={"type": "object"}, poll_timeout=None
    )
    assert rows(dataset)[0]["generated_json"]["summary"] == "s"


def test_wire_discover_returns_json(client) -> None:
    client.wire.discover.return_value = [
        WireActionMatch.model_validate({"action_id": "hn_search", "catalog_slug": "hackernews"})
    ]
    result = call("wire_discover", q="hn", limit=1)
    client.wire.discover.assert_called_once_with("hn", catalog=None, limit=1)
    assert result[0]["action_id"] == "hn_search"
    json.dumps(result)


def test_wire_read_writes_result_and_metadata(client, dataset) -> None:
    client.wire.run.return_value = WireResult(
        job_id="w", status="completed", data={"x": 1}, credits_used=2
    )
    call("wire_read_action", result=dataset, action_id="a", params={"q": "z"})
    client.wire.run.assert_called_once_with(
        "a", {"q": "z"}, credential_id=None, identity_id=None, poll_timeout=None
    )
    assert rows(dataset)[0]["data"] == {"x": 1}
    assert dataset.metadata["credits_used"] == 2


@pytest.mark.parametrize(
    ("action_id", "params"),
    [
        ("amazon_checkout", {}),
        ("post_form", {"note": "please pay now"}),
        ("place-order", {}),
    ],
)
def test_wire_write_refuses_payments_before_any_call(client, action_id, params) -> None:
    with pytest.raises(ValueError, match="payments or fund transfers"):
        call("wire_write_action", action_id=action_id, params=params)
    client.wire.run.assert_not_called()


def test_wire_write_runs_benign_actions(client) -> None:
    client.wire.run.return_value = WireResult(job_id="w", status="completed")
    assert call("wire_write_action", action_id="add_to_cart")["status"] == "completed"


def test_financial_check_can_be_turned_off(monkeypatch) -> None:
    monkeypatch.setenv("ANAKIN_ALLOW_FINANCIAL", "true")
    refuse_if_financial("amazon_checkout")


def test_wire_login_reads_secrets_from_the_environment(client, monkeypatch) -> None:
    monkeypatch.setenv("SITE_PASSWORD", "hunter2")
    client.wire.login.return_value = WireLoginResult(
        status="ok", identity_id="i", credential_id="cred"
    )
    result = call(
        "wire_login",
        catalog_slug="site",
        params={"email": "a@b.c"},
        params_from_env={"password": "SITE_PASSWORD"},
    )
    assert client.wire.login.call_args.args[1] == {"email": "a@b.c", "password": "hunter2"}
    assert result["credential_id"] == "cred"
    assert "hunter2" not in json.dumps(result)


def test_wire_login_fails_on_a_missing_variable(client, monkeypatch) -> None:
    monkeypatch.delenv("SITE_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="SITE_PASSWORD"):
        call("wire_login", catalog_slug="s", params_from_env={"password": "SITE_PASSWORD"})
    client.wire.login.assert_not_called()


def test_wire_build_refuses_payment_goals(client) -> None:
    with pytest.raises(ValueError):
        call("wire_build", website_url="https://a.io", goal="complete checkout")
    client.wire.build.assert_not_called()


MONITOR = {"id": "m1", "url": "https://a.io", "alert_webhook_secret": "whsec_x"}


def monitor():
    return Monitor.model_validate(MONITOR)


def test_monitor_create_redacts_and_drops_unset_options(client) -> None:
    client.monitors.create.return_value = monitor()
    result = call("monitor_create", url="https://a.io", interval_minutes=60, ai_goal="prices")
    args, kwargs = client.monitors.create.call_args
    assert args == ("https://a.io", 60)
    assert kwargs["ai_goal"] == "prices"
    assert "session_id" not in kwargs
    assert "whsec_x" not in json.dumps(result)


def test_monitor_list_and_get_redact(client) -> None:
    client.monitors.list.return_value = [monitor()]
    client.monitors.get.return_value = monitor()
    assert "whsec_x" not in json.dumps(call("monitor_list"))
    assert "whsec_x" not in json.dumps(call("monitor_get", monitor_id="m1"))


def test_redact_leaves_monitors_without_a_secret_alone() -> None:
    assert redact_webhook_secret({"id": "m"}) == {"id": "m"}


def test_monitor_changes_writes_rows(client, dataset) -> None:
    client.monitors.changes.return_value = [MonitorChange(id="c1"), MonitorChange(id="c2")]
    call("monitor_changes", changes=dataset, monitor_id="m1")
    assert [r["id"] for r in rows(dataset)] == ["c1", "c2"]


@pytest.mark.parametrize("action", ["pause", "resume"])
def test_monitor_control_redacts(client, action) -> None:
    getattr(client.monitors, action).return_value = monitor()
    result = call("monitor_control", monitor_id="m1", action=action)
    getattr(client.monitors, action).assert_called_once_with("m1")
    assert "whsec_x" not in json.dumps(result)


def test_monitor_control_run_now(client) -> None:
    client.monitors.run_now.return_value = MonitorRun.model_validate(
        {"success": True, "job_id": "j", "message": "queued"}
    )
    assert call("monitor_control", monitor_id="m1", action="run_now")["job_id"] == "j"


def test_monitor_control_delete_returns_a_dict(client) -> None:
    assert call("monitor_control", monitor_id="m1", action="delete") == {"deleted": True}
    client.monitors.delete.assert_called_once_with("m1")


def test_monitor_control_rejects_unknown_actions(client) -> None:
    with pytest.raises(ValueError, match="Unknown monitor action"):
        call("monitor_control", monitor_id="m1", action="explode")


def test_ai_visibility_sources(client) -> None:
    client.ai_visibility.sources.return_value = [
        AIVisibilitySource.model_validate({"slug": "chatgpt", "name": "ChatGPT"})
    ]
    assert call("ai_visibility_sources")[0]["slug"] == "chatgpt"


@pytest.mark.parametrize(("keep", "expected"), [(False, None), (True, "long")])
def test_ai_visibility_full_content(client, dataset, keep, expected) -> None:
    client.ai_visibility.search.return_value = AIVisibilitySearch.model_validate(
        {
            "search_id": "s",
            "status": "completed",
            "results": [{"source": "chatgpt", "status": "completed", "full_content": "long"}],
        }
    )
    call("ai_visibility_search", result=dataset, query="q", include_full_content=keep)
    assert rows(dataset)[0]["results"][0]["full_content"] == expected
    assert dataset.metadata["search_id"] == "s"


def test_session_delete(client) -> None:
    assert call("session_delete", session_id="s1") is None
    client.sessions.delete.assert_called_once_with("s1")


class TestBrowserTask:
    def transport(self, responses, seen):
        queue = iter(responses)

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            status, body = next(queue)
            return httpx.Response(status, json=body)

        return httpx.MockTransport(handler)

    def patched(self, responses, seen):
        real = httpx.Client
        transport = self.transport(responses, seen)
        return mock.patch("httpx.Client", lambda **kw: real(transport=transport, **kw))

    def test_needs_a_key(self, monkeypatch) -> None:
        monkeypatch.delenv("ANAKIN_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key"):
            call("browser_task", prompt="find the title")

    def test_refuses_payments(self, monkeypatch) -> None:
        monkeypatch.setenv("ANAKIN_API_KEY", "k")
        with pytest.raises(ValueError, match="payments"):
            call("browser_task", prompt="complete the checkout")

    def test_polls_until_complete(self, monkeypatch) -> None:
        monkeypatch.setenv("ANAKIN_API_KEY", "k")
        seen: list = []
        responses = [
            (200, {"workflow_id": "w1"}),
            (
                200,
                {
                    "status": "completed",
                    "result": {"success": True, "result": "ok", "steps": [1, 2], "run_id": "r"},
                },
            ),
        ]
        with self.patched(responses, seen):
            result = call("browser_task", prompt="find the title", url="https://a.io", max_steps=3)
        assert result["result"] == "ok"
        assert result["steps_taken"] == 2
        body = json.loads(seen[0].content)
        assert body == {
            "prompt": "find the title",
            "async": True,
            "url": "https://a.io",
            "max_steps": 3,
        }
        assert seen[0].headers["X-API-Key"] == "k"
        assert seen[1].url.path == "/v1/ai/jobs/w1"

    def test_failed_job_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("ANAKIN_API_KEY", "k")
        seen: list = []
        responses = [(200, {"workflow_id": "w"}), (200, {"status": "failed", "error": "nope"})]
        with self.patched(responses, seen), pytest.raises(RuntimeError, match="nope"):
            call("browser_task", prompt="find the title")

    def test_failed_job_reports_the_reason_in_result(self, monkeypatch) -> None:
        monkeypatch.setenv("ANAKIN_API_KEY", "k")
        seen: list = []
        responses = [
            (200, {"workflow_id": "w"}),
            (200, {"status": "failed", "result": {"success": False, "result": "planner failed"}}),
        ]
        with self.patched(responses, seen), pytest.raises(RuntimeError, match="planner failed"):
            call("browser_task", prompt="find the title")

    def test_http_error_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("ANAKIN_API_KEY", "k")
        seen: list = []
        with (
            self.patched([(402, {"error": "no credits"})], seen),
            pytest.raises(RuntimeError, match="402"),
        ):
            call("browser_task", prompt="find the title")
