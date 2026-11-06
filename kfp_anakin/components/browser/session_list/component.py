"""List saved browser sessions (logged-in states you created in the Anakin dashboard)."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def session_list(domain: str = None) -> list:
    """List saved browser sessions (logged-in states you created in the Anakin dashboard).

    Pass a session's id as session_id to scrape_url, crawl_site, monitor_create or
    browser_task to run as that logged-in user.

    Args:
        domain: Only sessions for this domain, e.g. "amazon.com".

    Returns:
        Sessions with id, name, website_domain and is_active.
    """
    from anakin import Anakin

    return to_json(Anakin().sessions.list(domain=domain))
