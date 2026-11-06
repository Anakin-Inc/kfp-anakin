"""List the AI answer engines ai_visibility_search can query."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def ai_visibility_sources() -> list:
    """List the AI answer engines ai_visibility_search can query.

    Returns:
        Each engine's slug (pass these as sources) and display name.
    """
    from anakin import Anakin

    return to_json(Anakin().ai_visibility.sources())
