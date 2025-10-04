from __future__ import annotations

from typing import Dict, Generic, Hashable, Optional, Tuple, TypeVar

T = TypeVar("T")


class ResultCache(Generic[T]):
    """Simple in-memory cache keyed by hashable input tuples."""

    def __init__(self) -> None:
        self._store: Dict[Hashable, Tuple[T, ...]] = {}

    def get(self, key: Hashable) -> Optional[Tuple[T, ...]]:
        return self._store.get(key)

    def set(self, key: Hashable, value: Tuple[T, ...]) -> None:
        self._store[key] = value
