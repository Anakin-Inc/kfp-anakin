"""AI web search with citations. Synchronous."""

from typing import NamedTuple

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def search(prompt: str, limit: int = 5) -> NamedTuple(
    "Outputs", [("urls", list), ("results", list)]
):
    """AI web search with citations. Synchronous.

    Pass `urls` to dsl.ParallelFor to fan scrape_url out over the results.

    Args:
        prompt: The search query or question.
        limit: Maximum results (max 20).

    Returns:
        urls: The result URLs. results: One entry per result, with url, title, snippet
        and date.
    """
    from collections import namedtuple

    from anakin import Anakin

    result = Anakin().search(prompt, limit=limit)
    Outputs = namedtuple("Outputs", ["urls", "results"])
    return Outputs([item.url for item in result.results], to_json(result.results))
