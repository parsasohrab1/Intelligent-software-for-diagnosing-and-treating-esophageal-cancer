"""
Uniform pagination for list endpoints.
Standard: offset/limit with a single max page size across all lists.
"""
from typing import Optional

# Standard pagination constants (use in all list endpoints)
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100


def clamp_limit(limit: Optional[int] = None) -> int:
    """Return limit clamped to [1, MAX_PAGE_SIZE]; default DEFAULT_PAGE_SIZE."""
    if limit is None:
        return DEFAULT_PAGE_SIZE
    return max(1, min(int(limit), MAX_PAGE_SIZE))


def pagination_params(
    offset: int = 0,
    limit: Optional[int] = None,
) -> tuple[int, int]:
    """Return (offset, effective_limit). offset must be >= 0; limit is clamped."""
    safe_offset = max(0, int(offset))
    effective_limit = clamp_limit(limit)
    return safe_offset, effective_limit
