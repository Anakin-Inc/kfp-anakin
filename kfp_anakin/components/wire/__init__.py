"""Wire: pre-built actions on hundreds of sites."""

from kfp_anakin.components.wire.wire_build.component import wire_build
from kfp_anakin.components.wire.wire_build_status.component import wire_build_status
from kfp_anakin.components.wire.wire_catalog.component import wire_catalog
from kfp_anakin.components.wire.wire_catalogs.component import wire_catalogs
from kfp_anakin.components.wire.wire_discover.component import wire_discover
from kfp_anakin.components.wire.wire_identities.component import wire_identities
from kfp_anakin.components.wire.wire_login.component import wire_login
from kfp_anakin.components.wire.wire_read_action.component import wire_read_action
from kfp_anakin.components.wire.wire_write_action.component import wire_write_action

__all__ = [
    "wire_build",
    "wire_build_status",
    "wire_catalog",
    "wire_catalogs",
    "wire_discover",
    "wire_identities",
    "wire_login",
    "wire_read_action",
    "wire_write_action",
]
