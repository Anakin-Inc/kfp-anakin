"""Run components with KFP's local runner against api.anakin.io. Skipped unless ANAKIN_LIVE_TESTS=1.

Each component installs anakin-sdk into a fresh venv, exactly as the embedded
code does in a pod. The keyless tests need no API key; the rest only read
account state and run when ANAKIN_API_KEY is set too.
"""

import json
import os

import pytest
from kfp import local

import kfp_anakin

pytestmark = pytest.mark.skipif(
    os.environ.get("ANAKIN_LIVE_TESTS") != "1",
    reason="set ANAKIN_LIVE_TESTS=1 to call the live API",
)
needs_key = pytest.mark.skipif(not os.environ.get("ANAKIN_API_KEY"), reason="needs ANAKIN_API_KEY")


@pytest.fixture(autouse=True)
def local_runner(tmp_path):
    local.init(runner=local.SubprocessRunner(use_venv=True), pipeline_root=str(tmp_path))


def test_scrape_keyless(monkeypatch) -> None:
    monkeypatch.delenv("ANAKIN_API_KEY", raising=False)
    task = kfp_anakin.scrape_url(url="https://example.com")
    with open(task.outputs["document"].path, encoding="utf-8") as lines:
        row = json.loads(lines.readline())
    assert row["status"] == "completed"
    assert "documentation examples" in row["markdown"]


def test_wire_lookup_keyless(monkeypatch) -> None:
    monkeypatch.delenv("ANAKIN_API_KEY", raising=False)
    assert kfp_anakin.wire_discover(q="search hacker news", limit=2).output
    assert kfp_anakin.wire_catalogs().output


@needs_key
def test_search_with_key() -> None:
    assert kfp_anakin.search(prompt="kubeflow pipelines", limit=2).outputs["urls"]


@needs_key
def test_account_reads_with_key() -> None:
    assert kfp_anakin.ai_visibility_sources().output
    assert isinstance(kfp_anakin.monitor_list().output, list)
    assert isinstance(kfp_anakin.session_list().output, list)
    assert isinstance(kfp_anakin.wire_identities().output, list)
