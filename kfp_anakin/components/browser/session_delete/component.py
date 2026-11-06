"""Permanently delete a saved browser session and its encrypted login data."""

from kfp import dsl

from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
)
def session_delete(session_id: str):
    """Permanently delete a saved browser session and its encrypted login data.

    Anything that uses this session loses its logged-in access. Turn caching off on this
    task.

    Args:
        session_id: The session's id, from session_list.
    """
    from anakin import Anakin

    Anakin().sessions.delete(session_id)
