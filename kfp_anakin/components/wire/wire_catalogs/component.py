"""List every site in the Wire catalog with its action count."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def wire_catalogs() -> list:
    """List every site in the Wire catalog with its action count.

    Works without an API key.

    Returns:
        One entry per site. Pass its slug to wire_catalog.
    """
    from anakin import Anakin

    return to_json(Anakin().wire.catalogs())
