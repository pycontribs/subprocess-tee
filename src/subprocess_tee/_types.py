"""Internally used types."""

from os import PathLike
from typing import Union

StrOrBytesPath = Union[str, bytes, PathLike[str], PathLike[bytes]]
