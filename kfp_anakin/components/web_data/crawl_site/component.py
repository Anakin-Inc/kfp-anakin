"""Fetch markdown for many pages of a site in one job."""

from kfp import dsl

from kfp_anakin._helpers import to_json, write_jsonl
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[write_jsonl, to_json],
)
def crawl_site(
    pages: dsl.Output[dsl.Dataset],
    url: str,
    max_pages: int = 10,
    depth: int = 1,
    include_patterns: list = None,
    exclude_patterns: list = None,
    country: str = "us",
    use_browser: bool = False,
    session_id: str = None,
    poll_timeout: float = None,
):
    """Fetch markdown for many pages of a site in one job.

    Args:
        pages: JSONL Dataset with one row per page (url, status, markdown, error). Its
            metadata has job_id, status, total_pages and completed_pages.
        url: Starting URL.
        max_pages: Maximum pages fetched.
        depth: Link hops to follow from url.
        include_patterns: Only fetch URLs matching at least one of these patterns.
        exclude_patterns: Skip URLs matching any of these patterns.
        country: Proxy country code.
        use_browser: Render each page with a headless browser.
        session_id: Saved browser session to crawl as a logged-in user.
        poll_timeout: Seconds to wait for the job (SDK default: 300).
    """
    from anakin import Anakin

    result = Anakin().crawl(
        url,
        max_pages=max_pages,
        depth=depth,
        include_patterns=include_patterns or (),
        exclude_patterns=exclude_patterns or (),
        country=country,
        use_browser=use_browser,
        session_id=session_id,
        poll_timeout=poll_timeout,
    )
    write_jsonl(pages, [to_json(page) for page in result.pages])
    pages.metadata.update(
        {
            "job_id": result.id,
            "status": result.status,
            "total_pages": result.total_pages,
            "completed_pages": result.completed_pages,
        }
    )
