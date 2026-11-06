"""Pause, resume, run, or delete a monitor. Turn caching off on this task."""

from kfp import dsl

from kfp_anakin._helpers import redact_webhook_secret, to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json, redact_webhook_secret],
)
def monitor_control(monitor_id: str, action: str) -> dict:
    """Pause, resume, run, or delete a monitor. Turn caching off on this task.

    Args:
        monitor_id: The monitor's id.
        action: "pause", "resume", "run_now" (an immediate check, billed like a scheduled
            one) or "delete" (removes the monitor and its history).

    Returns:
        The updated monitor for pause/resume, the queued run (success, job_id, message)
        for run_now, and {"deleted": true} for delete.
    """
    from anakin import Anakin

    monitors = Anakin().monitors
    if action == "delete":
        monitors.delete(monitor_id)
        return {"deleted": True}
    calls = {"pause": monitors.pause, "resume": monitors.resume, "run_now": monitors.run_now}
    if action not in calls:
        raise ValueError(
            f"Unknown monitor action {action!r}: use one of pause, resume, run_now, delete."
        )
    return redact_webhook_secret(to_json(calls[action](monitor_id)))
