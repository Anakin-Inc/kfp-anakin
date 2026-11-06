"""List your website monitors."""

from kfp import dsl

from kfp_anakin._helpers import redact_webhook_secret, to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json, redact_webhook_secret],
)
def monitor_list() -> list:
    """List your website monitors.

    Returns:
        Every monitor, with webhook signing secrets redacted.
    """
    from anakin import Anakin

    return [redact_webhook_secret(to_json(m)) for m in Anakin().monitors.list()]
