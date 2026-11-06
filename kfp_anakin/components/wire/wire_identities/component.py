"""List your saved Wire identities (site accounts) and their credentials."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def wire_identities(catalog_id: str = None) -> list:
    """List your saved Wire identities (site accounts) and their credentials.

    Args:
        catalog_id: Only identities for this catalog.

    Returns:
        Identities, each with credentials. A credential's id can be passed as
        credential_id to the Wire action components.
    """
    from anakin import Anakin

    return to_json(Anakin().wire.identities(catalog_id=catalog_id))
