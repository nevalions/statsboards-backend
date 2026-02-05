# Patterns

## Schema Structure

- Base → Create → Update → Output
- Output schemas use `model_config = ConfigDict(from_attributes=True)`
- Use `from __future__ import annotations` in schema files

## Avoid Circular Imports

Use `TYPE_CHECKING` blocks and string annotations for related schemas:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from src.matches.schemas import MatchSchema


class TeamWithMatchesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    matches: list["MatchSchema"]
```

## Eager Loading

- Use `selectinload()` for most relationships
- Use `joinedload()` for single relationships
- Chain `selectinload()` for deeper nesting

## Pagination Wrappers

Paginated responses should use `PaginationMetadata` from `src/core/schema_helpers.py`.
