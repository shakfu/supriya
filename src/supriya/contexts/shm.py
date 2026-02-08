"""
Server shared memory interface.

Thin Python wrapper around the nanobind _shm extension that preserves
the Bus/BusGroup dispatch logic from the original Cython implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from supriya._shm import ServerSHM as _ServerSHM

if TYPE_CHECKING:
    from .entities import Bus, BusGroup


class ServerSHM:
    """Server shared memory interface."""

    def __init__(self, port_number: int, bus_count: int) -> None:
        self._impl = _ServerSHM(port_number, bus_count)

    @overload
    def __getitem__(self, item: Bus | int) -> float: ...

    @overload
    def __getitem__(self, item: BusGroup | slice) -> list[float]: ...

    def __getitem__(self, item):
        from .entities import Bus, BusGroup

        if isinstance(item, Bus):
            item = int(item)
        elif isinstance(item, BusGroup):
            item = slice(int(item), int(item) + len(item))
        if isinstance(item, int):
            return self._impl.get_bus(item)
        elif isinstance(item, slice):
            start, stop, step = item.indices(self._impl.bus_count)
            return self._impl.get_bus_range(start, stop, step)
        raise ValueError(item)

    @overload
    def __setitem__(self, item: Bus | int, value: float) -> None: ...

    @overload
    def __setitem__(self, item: BusGroup | slice, value: list[float]) -> None: ...

    def __setitem__(self, item, value):
        from .entities import Bus, BusGroup

        if isinstance(item, BusGroup):
            item = slice(int(item), int(item) + len(item), 1)
        elif isinstance(item, Bus):
            item = int(item)
        if isinstance(item, int):
            self._impl.set_bus(item, float(value))
            return
        elif isinstance(item, slice):
            start, stop, step = item.indices(self._impl.bus_count)
            self._impl.set_bus_range(start, stop, step, [float(v) for v in value])
            return
        raise ValueError(item, value)

    def describe_scope_buffer(self, index: int) -> tuple[int, int]:
        return self._impl.describe_scope_buffer(index)

    def read_scope_buffer(self, index: int) -> tuple[int, list[float]]:
        return self._impl.read_scope_buffer(index)
