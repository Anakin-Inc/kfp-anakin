"""Scrape one URL to markdown, optionally extracting structured JSON with AI."""

from kfp import dsl

from kfp_anakin._helpers import to_json, write_jsonl
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[write_jsonl, to_json],
)
def scrape_url(
    document: dsl.Output[dsl.Dataset],
    url: str,
    country: str = "us",
    use_browser: bool = False,
    generate_json: bool = False,
    output_schema: dict = None,
    formats: list = None,
    force_fresh: bool = False,
    session_id: str = None,
    session_name: str = None,
    poll_timeout: float = None,
):
    """Scrape one URL to markdown, optionally extracting structured JSON with AI.

    Works without an API key on a small free per-IP allowance.

    Args:
        document: JSONL Dataset with one row: the scraped document (markdown,
            generated_json, html and more). Its metadata has job_id, status and cached.
        url: The URL to scrape.
        country: Proxy country code, e.g. "us", "gb", "de".
        use_browser: Render with a headless browser. Use for JavaScript-heavy pages.
        generate_json: Extract structured JSON from the page with AI.
        output_schema: JSON Schema for the extracted JSON (implies AI extraction).
        formats: Output formats, any of "markdown" (default), "html", "cleaned_html",
            "screenshot", "links".
        force_fresh: Skip Anakin's cache and fetch the page again.
        session_id: Saved browser session to scrape as a logged-in user.
        session_name: Saved browser session name (alternative to session_id).
        poll_timeout: Seconds to wait for the job (SDK default: 300).
    """
    from anakin import Anakin

    result = Anakin().scrape(
        url,
        formats=tuple(formats or ("markdown",)),
        country=country,
        use_browser=use_browser,
        generate_json=generate_json,
        output_schema=output_schema,
        force_fresh=force_fresh,
        session_id=session_id,
        session_name=session_name,
        poll_timeout=poll_timeout,
    )
    write_jsonl(document, [to_json(result)])
    document.metadata.update(
        {"job_id": result.id, "status": result.status, "cached": result.cached}
    )
