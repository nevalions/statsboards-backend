# Testing and Errors

## Common Errors

**Circular import errors** usually mean schema imports are not under `TYPE_CHECKING` or string annotations are missing.

Bad:

```python
from src.matches.schemas import MatchSchema
class TeamWithMatchesSchema(BaseModel):
    matches: list[MatchSchema]
```

Good:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.matches.schemas import MatchSchema

class TeamWithMatchesSchema(BaseModel):
    matches: list["MatchSchema"]
```

## Testing

- Test both success and missing related data paths
- Ensure eager-loading paths match schema needs
- Verify pagination metadata when using combined schemas in lists
