"""Fetch one monitor's configuration and status."""

from kfp import dsl

from kfp_anakin._helpers import redact_webhook_secret, to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json, redact_webhook_secret],
)
def monitor_get(monitor_id: str) -> dict:
    """Fetch one monitor's configuration and status.

    Args:
        monitor_id: The monitor's id.

    Returns:
        The monitor, with its webhook signing secret redacted.
    """
    from anakin import Anakin

    return redact_webhook_secret(to_json(Anakin().monitors.get(monitor_id)))
