"""Internally used types."""

# Source from https://github.com/python/typing/issues/256#issuecomment-1442633430
from collections.abc import Iterator, Sequence
from typing import Any, Protocol, SupportsIndex, TypeVar, overload

_T_co = TypeVar("_T_co", covariant=True)


class SequenceNotStr(Protocol[_T_co]):
    """Lists of strings which are not strings themselves."""

    @overload
    def __getitem__(self, index: SupportsIndex, /) -> _T_co: ...
    @overload
    def __getitem__(self, index: slice, /) -> Sequence[_T_co]: ...
    def __contains__(self, value: object, /) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[_T_co]: ...
    def index(  # pylint: disable=C0116
        self, value: Any, start: int = 0, stop: int = ..., /
    ) -> int: ...
    def count(self, value: Any, /) -> int: ...  # pylint: disable=C0116

    def __reversed__(self) -> Iterator[_T_co]: ...
