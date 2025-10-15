from __future__ import annotations

from . import hue  # noqa: F401
from . import cast  # noqa: F401
from . import sonos  # noqa: F401
from . import mqtt_handler  # noqa: F401
from . import http_handler  # noqa: F401
from . import printer  # noqa: F401
from . import upnp_handler  # noqa: F401
from . import ssh_handler  # noqa: F401
from . import home_assistant  # noqa: F401
from . import matter  # noqa: F401

__all__ = ['registry']
