"""Multi-step research: search, scrape the cited pages, return a structured answer."""

from kfp import dsl

from kfp_anakin._helpers import to_json, write_jsonl
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[write_jsonl, to_json],
)
def agentic_search(
    result: dsl.Output[dsl.Dataset],
    prompt: str,
    use_browser: bool = True,
    schema: dict = None,
    poll_timeout: float = None,
):
    """Multi-step research: search, scrape the cited pages, return a structured answer.

    Takes minutes rather than seconds. Use search for quick lookups.

    Args:
        result: JSONL Dataset with one row: status and generated_json (summary,
            structured_data and data_schema). Its metadata has job_id and status.
        prompt: The research question (max 8 KB).
        use_browser: Scrape citations with a headless browser.
        schema: JSON Schema (max 50 KB) for structured_data.
        poll_timeout: Seconds to wait for the job (SDK default: 300).
    """
    from anakin import Anakin

    answer = Anakin().agentic_search(
        prompt, use_browser=use_browser, schema=schema, poll_timeout=poll_timeout
    )
    write_jsonl(result, [to_json(answer)])
    result.metadata.update({"job_id": answer.id, "status": answer.status})
