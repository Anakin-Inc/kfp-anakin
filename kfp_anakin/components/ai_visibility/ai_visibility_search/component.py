"""Ask several AI answer engines (ChatGPT, Gemini, Google AI Overview, ...) one question."""

from kfp import dsl

from kfp_anakin._helpers import to_json, write_jsonl
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[write_jsonl, to_json],
)
def ai_visibility_search(
    result: dsl.Output[dsl.Dataset],
    query: str,
    sources: list = None,
    country: str = "us",
    include_full_content: bool = False,
    poll_timeout: float = None,
):
    """Ask several AI answer engines (ChatGPT, Gemini, Google AI Overview, ...) one question.

    Useful for checking how a brand or topic shows up in AI answers, per country. Billed
    per engine that answers; failed engines are free. A search where some engines failed
    is returned, not raised.

    Args:
        result: JSONL Dataset with one row: search_id, status, synthesis and one results
            entry per engine. Its metadata has search_id and status.
        query: The question (max 2000 characters).
        sources: Engine slugs from ai_visibility_sources. Omit for all.
        country: Two-letter country code for the search location.
        include_full_content: Keep each engine's full answer text. Off by default;
            summaries and the cross-engine synthesis are always returned.
        poll_timeout: Seconds to wait for the search (SDK default: 300).
    """
    from anakin import Anakin

    answer = Anakin().ai_visibility.search(
        query, sources=sources, country=country, poll_timeout=poll_timeout
    )
    row = to_json(answer)
    if not include_full_content:
        for engine in row.get("results", []):
            engine["full_content"] = None
    write_jsonl(result, [row])
    result.metadata.update({"search_id": answer.search_id, "status": answer.status})
