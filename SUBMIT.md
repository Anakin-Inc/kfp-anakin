# kfp-anakin: status and release steps

Not shipped in the sdist (excluded in `pyproject.toml`).

## Route

KEP-913 makes vendor components a non-goal for `kubeflow/pipelines-components` and asks vendors to
use the same structure in their own repository. So: a PyPI package plus an install guide at
anakin.io/docs/integrations/workflow/kubeflow. No Kubeflow-side listing.

## Layout

Same as the catalog (category/component with `component.py`, `metadata.yaml`, `README.md`). Two
deliberate differences: one root `OWNERS` instead of 24 identical copies, and tests in one `tests/`
directory. Component `metadata.yaml` and `README.md` are generated.

## Verified (2026-11-06)

- `pytest` on kfp 2.15.2 / Python 3.10, kfp 2.18.0 / Python 3.12 and kfp 2.18.0 / Python 3.13.
- `ruff`, `mypy`, `uv build`, `twine check --strict`, clean-venv wheel install (no anakin-sdk needed).
- KFP `SubprocessRunner` and `DockerRunner` (real `python:3.11-slim`) against the live API.
- Real cluster: kind, KFP 2.15.0 backend, kfp SDK 2.18.0. `web_to_dataset` (`ParallelFor` +
  `Collected`, 2 rows merged from 2 URLs), `keyless_scrape`, a mixed run (`map_site`, `wire_discover`,
  `wire_catalog`) and the docs' Wire snippet (pipeline input inside `params`) all succeeded.
- Secret: `ANAKIN_API_KEY` set by `secretKeyRef` only on wrapped tasks; key absent from pod logs. No
  key fails with the SDK's `ConfigurationError`. A missing secret gives `CreateContainerConfigError`.
- Caching is on by default: a second default run skipped the executor (no new pod).
- Live calls: `crawl_site`, `agentic_search`, `wire_catalogs`, `ai_visibility_sources`, and a monitor
  create/get/changes/pause/delete cycle (test monitor removed).

## Not verified

- `browser_task` has not completed successfully live. The request and polling work, but on
  2026-11-06 the job failed on Anakin's side: planner HTTP 402 from OpenRouter (credits).
- `wire_write_action`, `wire_login`, `wire_build`, `session_delete`, `ai_visibility_search`: unit
  tests only, to avoid changing account state or spending credits.
- A full Kubeflow Platform install (multi-user, Istio). Only standalone KFP was run.

## Release

1. Add a PyPI pending publisher: project `kfp-anakin`, owner `Anakin-Inc`, repository `kfp-anakin`,
   workflow `publish.yml`, environment `pypi`.
2. Push tag `v0.1.0`. The tag must match `kfp_anakin/_version.py`.
3. Check `pip index versions kfp-anakin`.
