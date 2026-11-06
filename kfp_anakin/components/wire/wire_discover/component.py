"""Find Wire actions for a task described in plain language."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def wire_discover(q: str, catalog: str = None, limit: int = None) -> list:
    """Find Wire actions for a task described in plain language.

    Works without an API key.

    Args:
        q: What you want to do, e.g. "top phones on walmart".
        catalog: Restrict to one site's catalog slug, e.g. "amazon".
        limit: Maximum candidate actions to return.

    Returns:
        Ranked actions, each with action_id, catalog_slug, params and credits.
    """
    from anakin import Anakin

    return to_json(Anakin().wire.discover(q, catalog=catalog, limit=limit))
