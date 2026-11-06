"""Check a Wire build request started with wire_build."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def wire_build_status(build_id: str) -> dict:
    """Check a Wire build request started with wire_build.

    Turn caching off on this task, or every poll returns the first answer.

    Args:
        build_id: The id returned by wire_build.

    Returns:
        The build's status and, once published, its action_id.
    """
    from anakin import Anakin

    return to_json(Anakin().wire.get_build(build_id))
