"""Discover the URLs on a site (sitemap plus link traversal)."""

from typing import NamedTuple

from kfp import dsl

from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
)
def map_site(
    url: str,
    limit: int = 100,
    depth: int = 2,
    limit_per_level: int = 100,
    include_subdomains: bool = False,
    include_external_links: bool = False,
    search: str = None,
    use_browser: bool = False,
    session_id: str = None,
    poll_timeout: float = None,
) -> NamedTuple("Outputs", [("urls", list), ("total_links", int), ("external_urls", list)]):
    """Discover the URLs on a site (sitemap plus link traversal).

    Pass `urls` to dsl.ParallelFor to fan scrape_url out over the site.

    Args:
        url: Starting URL, usually a homepage or section root.
        limit: Maximum URLs to return (max 5000).
        depth: Link hops to follow from url (max 5).
        limit_per_level: Maximum URLs collected per depth level.
        include_subdomains: Include URLs on subdomains of the starting host.
        include_external_links: Also collect (but don't follow) external links.
        search: Only return URLs whose path or title matches this keyword.
        use_browser: Render with a headless browser. Needed for SPAs.
        session_id: Saved browser session to map as a logged-in user.
        poll_timeout: Seconds to wait for the job (SDK default: 300).

    Returns:
        urls: The URLs found. total_links: Their count. external_urls: External links,
        if requested.
    """
    from collections import namedtuple

    from anakin import Anakin

    result = Anakin().map(
        url,
        limit=limit,
        depth=depth,
        limit_per_level=limit_per_level,
        include_subdomains=include_subdomains,
        include_external_links=include_external_links,
        search=search,
        use_browser=use_browser,
        session_id=session_id,
        poll_timeout=poll_timeout,
    )
    Outputs = namedtuple("Outputs", ["urls", "total_links", "external_urls"])
    return Outputs(list(result.links), result.total_links, list(result.external_links))
