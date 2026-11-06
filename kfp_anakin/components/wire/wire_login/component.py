"""Sign in to a site that needs credentials and get a credential_id."""

from kfp import dsl

from kfp_anakin._helpers import to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json],
)
def wire_login(
    catalog_slug: str,
    params: dict = None,
    params_from_env: dict = None,
    identity_name: str = None,
    source_id: str = None,
    source_ref: dict = None,
) -> dict:
    """Sign in to a site that needs credentials and get a credential_id.

    Anakin stores the encrypted session, never the password. Kubeflow records task
    inputs and shows them in the UI, so never put a password in params. Mount it from a
    Kubernetes secret as an environment variable and name it in params_from_env, or use
    a 1Password source_id. Turn caching off on this task.

    Args:
        catalog_slug: The site to sign in to.
        params: Non-secret login fields listed in wire_catalog's login_input_schema.
        params_from_env: Login fields read from environment variables, as a mapping of
            field name to variable name, e.g. {"password": "SITE_PASSWORD"}.
        identity_name: Name for the identity.
        source_id: 1Password identity source, instead of params.
        source_ref: 1Password item locator (vault_id, item_id, fields), used with
            source_id.

    Returns:
        The login result, including the new credential_id.
    """
    import os

    from anakin import Anakin

    login_params = dict(params or {})
    for field, variable in (params_from_env or {}).items():
        if variable not in os.environ:
            raise ValueError(f"params_from_env: environment variable {variable} is not set.")
        login_params[field] = os.environ[variable]
    return to_json(
        Anakin().wire.login(
            catalog_slug,
            login_params or None,
            identity_name=identity_name,
            source_id=source_id,
            source_ref=source_ref,
        )
    )
