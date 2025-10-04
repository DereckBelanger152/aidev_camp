from __future__ import annotations

import unicodedata


class TextNormalizer:
    """Utility to normalize text for comparison purposes."""

    @staticmethod
    def normalize(value: str) -> str:
        """Return a lowercase, accent-free representation of the input string."""

        normalized = unicodedata.normalize("NFKD", value)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        return normalized.strip().casefold()
