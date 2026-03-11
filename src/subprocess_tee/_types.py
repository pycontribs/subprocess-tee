"""Internally used types."""

# Source from https://github.com/python/typing/issues/256#issuecomment-1442633430
from os import PathLike
from typing import TypeVar, Union

_T_co = TypeVar("_T_co", covariant=True)

StrOrBytesPath = Union[str, bytes, PathLike[str], PathLike[bytes]]
