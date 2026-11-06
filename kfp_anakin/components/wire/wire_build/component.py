"""Ask Anakin to build a new Wire action for a site that isn't in the catalog."""

from kfp import dsl

from kfp_anakin._helpers import refuse_if_financial, to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[refuse_if_financial, to_json],
)
def wire_build(
    website_url: str,
    goal: str,
    catalog_id: str = None,
    visibility: str = "private",
    force: bool = False,
) -> dict:
    """Ask Anakin to build a new Wire action for a site that isn't in the catalog.

    Builds run asynchronously: this returns the pending build request. Check on it with
    wire_build_status. Charges credits up front, refunded if the build fails. Run
    wire_discover first to make sure no action exists. Turn caching off on this task.
    Refuses payment or fund-transfer goals (raises ValueError).

    Args:
        website_url: The site to build an action for.
        goal: What the action should do or extract. Be specific.
        catalog_id: Attach to an existing catalog instead of creating one.
        visibility: "private" (default) or "public".
        force: Build even if similar actions already exist for the domain.

    Returns:
        The build request: id, status and related fields.
    """
    from anakin import Anakin

    refuse_if_financial(f"{goal} {website_url}")
    return to_json(
        Anakin().wire.build(
            website_url, goal, catalog_id=catalog_id, visibility=visibility, force=force
        )
    )
