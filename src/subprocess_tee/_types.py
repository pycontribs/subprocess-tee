"""Internally used types."""

# Source from https://github.com/python/typing/issues/256#issuecomment-1442633430
from collections.abc import Iterator, Sequence
from typing import Any, Protocol, SupportsIndex, TypeVar, overload, Union
from os import PathLike

_T_co = TypeVar("_T_co", covariant=True)

StrOrBytesPath = Union[str, bytes, PathLike[str], PathLike[bytes]]
