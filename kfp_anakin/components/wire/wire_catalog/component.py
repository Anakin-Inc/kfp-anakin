"""One Wire site's actions: parameter schema, mode, auth mode, credit cost."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def wire_catalog(slug: str) -> dict:
    """One Wire site's actions: parameter schema, mode, auth mode, credit cost.

    Works without an API key.

    Args:
        slug: The site, e.g. "walmart" (see wire_catalogs).

    Returns:
        The site's actions and, if it needs credentials, its login fields.
    """
    from anakin import Anakin

    return to_json(Anakin().wire.catalog(slug))
