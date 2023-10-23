import inspect
from typing import Any, TypeAlias

from pydantic.v1 import BaseModel
from spectree import Response
from spectree import SpecTree as _SpecTree
from spectree.config import SecurityScheme  # type: ignore
from spectree.models import SecureType, SecuritySchemeData

from finbot._version import __version__

SECURITY_SCHEME_NAME = "bearerAuth"
JWT_REQUIRED: dict[str, list[str]] = {SECURITY_SCHEME_NAME: []}


def get_model_key(model: type[BaseModel]) -> str:
    model_name_prefix = None
    model_module = inspect.getmodule(model)
    if model_module and (namespace := getattr(model_module, "SchemaNamespace", None)):
        model_name_prefix = namespace
    return f"{model_name_prefix or ''}{model.__name__}"


def get_nested_model_key(_: str, child_name: str) -> str:
    return child_name


DEFAULT_SPEC_TREE_CONFIG = dict(
    annotations=True,
    version=f"v{__version__}",
    path="apidoc",
    naming_strategy=get_model_key,
    nested_naming_strategy=get_nested_model_key,
    security_schemes=[
        SecurityScheme(
            name=SECURITY_SCHEME_NAME,
            data=SecuritySchemeData(  # type: ignore
                type=SecureType.HTTP,
                scheme="bearer",
                bearerFormat="JWT",
            ),
        )
    ],
)

ResponseSpec: TypeAlias = Response


def SpecTree(title: str, **spec_tree_kwargs: Any) -> _SpecTree:
    return _SpecTree(
        "flask", title=title, **{**DEFAULT_SPEC_TREE_CONFIG, **spec_tree_kwargs}
    )


__all__ = [
    "SpecTree",
    "ResponseSpec",
    "JWT_REQUIRED",
    "get_model_key",
    "get_nested_model_key",
]
