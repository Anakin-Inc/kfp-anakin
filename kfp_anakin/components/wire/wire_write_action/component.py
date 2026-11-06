"""Run a Wire write action: submit a form, add to cart, post content, update settings."""

from kfp import dsl

from kfp_anakin._helpers import refuse_if_financial, to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[refuse_if_financial, to_json],
)
def wire_write_action(
    action_id: str,
    params: dict = None,
    credential_id: str = None,
    identity_id: str = None,
    poll_timeout: float = None,
) -> dict:
    """Run a Wire write action: submit a form, add to cart, post content, update settings.

    Turn caching off on this task (task.set_caching_options(False)) and don't give it
    retries: repeating a write can duplicate it. Refuses (raises ValueError before
    calling the API) anything that looks like a payment or fund transfer.

    Args:
        action_id: The action to run, from wire_discover or wire_catalog.
        params: The action's parameters, as described by discovery.
        credential_id: Needed when the action's auth_mode is "required".
        identity_id: Alternative to credential_id: run as this saved identity.
        poll_timeout: Seconds to wait for the job (SDK default: 300).

    Returns:
        job_id, status, data, credits_used and error.
    """
    from anakin import Anakin

    resolved_params = params or {}
    refuse_if_financial(f"{action_id} {resolved_params}")
    return to_json(
        Anakin().wire.run(
            action_id,
            resolved_params,
            credential_id=credential_id,
            identity_id=identity_id,
            poll_timeout=poll_timeout,
        )
    )
