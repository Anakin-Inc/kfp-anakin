"""Get the changes a monitor has detected, newest first."""

from kfp import dsl

from kfp_anakin._helpers import to_json, write_jsonl
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[write_jsonl, to_json],
)
def monitor_changes(changes: dsl.Output[dsl.Dataset], monitor_id: str):
    """Get the changes a monitor has detected, newest first.

    Turn caching off on this task, or later runs return the first run's changes.

    Args:
        changes: JSONL Dataset with one row per detected change, with its diff and (when
            ai_mode is on) the AI summary.
        monitor_id: The monitor's id.
    """
    from anakin import Anakin

    write_jsonl(changes, [to_json(c) for c in Anakin().monitors.changes(monitor_id)])
