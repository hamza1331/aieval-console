"""Common schemas for pagination and shared response structures."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated envelope."""

    items: list[T] = Field(..., description="List of records for current page")
    total: int = Field(..., description="Total count matching query filter")
    limit: int = Field(..., description="Page item limit")
    offset: int = Field(..., description="Page offset")
