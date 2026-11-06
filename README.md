# kfp-anakin

[Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/) components for
[Anakin](https://anakin.io), a web data API. Scrape and crawl sites to markdown, run AI web search
and research, run pre-built Wire actions on hundreds of sites, watch pages for changes, and drive
an AI agent in a cloud browser, as steps in your pipelines.

This is a vendor package maintained by Anakin, not part of the Kubeflow project. Kubeflow's
[component catalog](https://github.com/kubeflow/pipelines-components) doesn't take vendor
components and [asks vendors](https://github.com/kubeflow/community/blob/master/proposals/913-components-repo/README.md)
to use the same repository structure in their own repository, which this one does.

## Install

```bash
pip install kfp-anakin
```

You need it where you compile pipelines, not on the cluster. Component code is embedded in the
compiled pipeline. Each task starts from `python:3.11-slim` and installs
[`anakin-sdk`](https://pypi.org/project/anakin-sdk/) when it starts, so task pods need outbound
access to PyPI and to `api.anakin.io`.

Requires Python 3.10+ and `kfp` 2.15.2+. Tested on a Kubeflow Pipelines 2.15.0 backend.

## Credentials

Get an API key at [anakin.io/dashboard](https://anakin.io/dashboard). The free tier needs no card.
Store it as a Kubernetes secret in the namespace your pipelines run in:

```bash
kubectl create secret generic anakin --from-literal=api-key=ask_... -n <namespace>
```

Then wrap each task that needs it in `with_api_key`, which sets `ANAKIN_API_KEY` from that secret.
Don't pass the key as a pipeline parameter: Kubeflow records and displays parameters.

With no key, `scrape_url`, `wire_discover`, `wire_catalogs` and `wire_catalog` still work on a small
free allowance, enough to try the package.

## Example

Search the web, scrape each result in parallel, and collect the pages into one dataset:

```python
from kfp import compiler, dsl
from kfp_anakin import scrape_url, search, with_api_key


@dsl.component(base_image="python:3.11-slim")
def merge_documents(
    documents: dsl.Input[list[dsl.Dataset]], merged: dsl.Output[dsl.Dataset]
) -> int:
    rows = 0
    with open(merged.path, "w", encoding="utf-8") as output:
        for document in documents:
            with open(document.path, encoding="utf-8") as lines:
                for line in lines:
                    output.write(line)
                    rows += 1
    return rows


@dsl.pipeline(name="anakin-web-to-dataset")
def web_to_dataset(prompt: str = "open source vector databases", limit: int = 3) -> dsl.Dataset:
    results = with_api_key(search(prompt=prompt, limit=limit))
    with dsl.ParallelFor(results.outputs["urls"], parallelism=3) as url:
        page = with_api_key(scrape_url(url=url)).set_caching_options(False)
    merged = merge_documents(documents=dsl.Collected(page.outputs["document"]))
    return merged.outputs["merged"]


compiler.Compiler().compile(web_to_dataset, "web_to_dataset.yaml")
```

Upload `web_to_dataset.yaml` in the Kubeflow Pipelines UI, or submit it with `kfp.Client`. See
[`examples/`](examples/) for this and a keyless pipeline.

## Components

| Component | What it does | Output |
|---|---|---|
| **Web data** | | |
| `scrape_url` | One page as markdown, optionally with HTML, a screenshot or AI-extracted JSON | `document` (Dataset) |
| `map_site` | Every URL on a site | `urls`, `total_links`, `external_urls` |
| `crawl_site` | Many pages of one site as markdown | `pages` (Dataset) |
| `search` | AI web search with citations | `urls`, `results` |
| `agentic_search` | Deep research across many sources: a summary plus structured data | `result` (Dataset) |
| **Wire: pre-built site actions** | | |
| `wire_discover` | Find actions for a task, e.g. "top phones on walmart" | list |
| `wire_catalogs` | Every supported site | list |
| `wire_catalog` | One site's actions and their parameters | dict |
| `wire_read_action` | Run an action that reads data | `result` (Dataset) |
| `wire_write_action` | Run an action that changes something on the site | dict |
| `wire_identities` | Your saved site logins | list |
| `wire_login` | Sign in to a site and get a credential | dict |
| `wire_build` | Request actions for a site Wire doesn't cover yet | dict |
| `wire_build_status` | Progress of a build request | dict |
| **Monitors** | | |
| `monitor_create` | Watch a page, a site or a Wire action on a schedule | dict |
| `monitor_list` | Your monitors | list |
| `monitor_get` | One monitor | dict |
| `monitor_changes` | Changes a monitor detected | `changes` (Dataset) |
| `monitor_control` | Pause, resume, run now or delete a monitor | dict |
| **AI visibility** | | |
| `ai_visibility_search` | Ask ChatGPT, Gemini and Google AI Overview one question and compare | `result` (Dataset) |
| `ai_visibility_sources` | The answer engines available | list |
| **Browser** | | |
| `session_list` | Saved browser sessions, for pages behind a login | list |
| `session_delete` | Delete a saved browser session | none |
| `browser_task` | An AI agent drives a real browser through a multi-step task | dict |

Each component's inputs are in its folder under
[`kfp_anakin/components/`](kfp_anakin/components/). Import from `kfp_anakin`, or from a category
such as `kfp_anakin.components.web_data`.

### Reading outputs

Page content goes into a `Dataset` artifact as JSON Lines, because Kubeflow keeps parameter outputs
in its metadata store. Read it in a downstream component:

```python
@dsl.component(base_image="python:3.11-slim")
def titles(document: dsl.Input[dsl.Dataset]) -> str:
    import json

    with open(document.path, encoding="utf-8") as lines:
        return json.loads(lines.readline())["markdown"][:80]
```

A component with one output uses `task.output`. With several, use `task.outputs["urls"]`. Dataset
metadata records the row count and the job's `job_id` and `status`.

## Caching and retries

Kubeflow caches a task by its inputs and **caching is on by default**, so a repeated run returns the
first run's output without calling Anakin. Turn it off with `task.set_caching_options(False)`:

- on reads that should be fresh (`scrape_url`, `monitor_changes`, `wire_build_status`...)
- on everything that changes state (`wire_write_action`, `wire_login`, `wire_build`,
  `monitor_create`, `monitor_control`, `session_delete`, and a `browser_task` that changes
  anything), otherwise a later run silently skips the write

Don't add `set_retry` to those write tasks either: repeating a write can duplicate it. The SDK
already retries rate limits and server errors.

## Logging in to sites

Kubeflow shows task inputs in its UI, so don't pass a password in `params`. Mount it from a
Kubernetes secret and name the variable in `params_from_env`:

```python
from kfp import kubernetes
from kfp_anakin import wire_login, with_api_key

login = with_api_key(
    wire_login(
        catalog_slug="example-site",
        params={"email": "me@example.com"},
        params_from_env={"password": "SITE_PASSWORD"},
    )
).set_caching_options(False)
kubernetes.use_secret_as_env(login, "site-login", {"password": "SITE_PASSWORD"})
```

## Payments

`wire_write_action`, `wire_build` and `browser_task` refuse anything that looks like it completes a
payment or moves money, the same rule as Anakin's MCP server. Benign writes such as "add to cart"
pass. To turn the check off, call `task.set_env_variable("ANAKIN_ALLOW_FINANCIAL", "true")`.

## Development

```bash
uv venv && uv pip install -e . --group test --group lint
uv run --no-sync pytest
uv run --no-sync ruff check . && uv run --no-sync mypy kfp_anakin
python scripts/gen_component_assets.py   # after changing a component
ANAKIN_LIVE_TESTS=1 uv run --no-sync pytest tests/test_live.py   # calls the live API
```

## License

Apache-2.0
