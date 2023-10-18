from typing import TypeAlias

from spectree import Response, SpecTree

from finbot._version import __version__

spec = SpecTree(
    "flask",
    title="Finbot application service",
    annotations=True,
    version=f"v{__version__}",
    path="apidoc",
)

ResponseSpec: TypeAlias = Response
