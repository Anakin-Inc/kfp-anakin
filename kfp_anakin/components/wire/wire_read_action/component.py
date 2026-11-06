"""Run a Wire read action, which extracts data without changing anything on the site."""

from kfp import dsl

from kfp_anakin._helpers import to_json, write_jsonl
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[write_jsonl, to_json],
)
def wire_read_action(
    result: dsl.Output[dsl.Dataset],
    action_id: str,
    params: dict = None,
    credential_id: str = None,
    identity_id: str = None,
    poll_timeout: float = None,
):
    """Run a Wire read action, which extracts data without changing anything on the site.

    For actions that change state, use wire_write_action.

    Args:
        result: JSONL Dataset with one row: job_id, status, data, credits_used and error.
            Its metadata has job_id, status and credits_used.
        action_id: The action to run, from wire_discover or wire_catalog.
        params: The action's parameters, as described by discovery.
        credential_id: Needed when the action's auth_mode is "required". Get one from
            wire_identities or wire_login.
        identity_id: Alternative to credential_id: run as this saved identity.
        poll_timeout: Seconds to wait for the job (SDK default: 300).
    """
    from anakin import Anakin

    run = Anakin().wire.run(
        action_id,
        params or {},
        credential_id=credential_id,
        identity_id=identity_id,
        poll_timeout=poll_timeout,
    )
    write_jsonl(result, [to_json(run)])
    result.metadata.update(
        {"job_id": run.job_id or "", "status": run.status, "credits_used": run.credits_used}
    )
