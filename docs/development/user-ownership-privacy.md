# User Ownership and Privacy

Several core models support user ownership and privacy controls.

## Models with Ownership and Privacy

- `TournamentDB`: `user_id`, `isprivate`
- `PlayerDB`: `user_id`, `isprivate`
- `PersonDB`: `owner_user_id`, `isprivate`
- `MatchDB`: `user_id`, `isprivate`
- `TeamDB`: `user_id`, `isprivate`

## Field Details

### user_id / owner_user_id

- Type: `Mapped[int]`
- Foreign Key: `user.id` with `ON DELETE SET NULL`
- Nullable: yes

### isprivate

- Type: `Mapped[bool]`
- Default: `False`
- Server default: `"false"`
- Nullable: no

## Model Pattern

```python
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .user import UserDB

class ExampleDB(Base):
    __tablename__ = "example"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", name="fk_example_user", ondelete="SET NULL"),
        nullable=True,
    )

    isprivate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    user: Mapped["UserDB"] = relationship(
        "UserDB",
        back_populates="examples",
    )
```

## Usage Patterns

### Filtering by User Ownership

```python
async def get_user_tournaments(user_id: int, session: AsyncSession) -> list[TournamentDB]:
    stmt = select(TournamentDB).where(TournamentDB.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Combining Ownership with Privacy

```python
async def get_accessible_players(user_id: int, session: AsyncSession) -> list[PlayerDB]:
    stmt = select(PlayerDB).where(
        (PlayerDB.user_id == user_id) | (~PlayerDB.isprivate)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
```

## Migration Notes

When adding ownership to new models:

1. Add FK with explicit name: `name="fk_{table}_user"`
2. Use `ondelete="SET NULL"`
3. Add `isprivate` with `default=False`, `server_default="false"`
4. Add bidirectional relationship in UserDB
5. Include constraint names in migrations

## Important Notes

- `PersonDB` uses `owner_user_id` instead of `user_id`
- All user FKs use `ON DELETE SET NULL`
- `isprivate` defaults to `false`
