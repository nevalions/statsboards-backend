# Examples

## Match With Details

Service method with eager loading:

```python
async def get_match_with_details(self, match_id: int) -> MatchDB | None:
    async with self.db.get_session_maker()() as session:
        stmt = (
            select(MatchDB)
            .where(MatchDB.id == match_id)
            .options(
                joinedload(MatchDB.team_a),
                joinedload(MatchDB.team_b),
                joinedload(MatchDB.tournaments),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

API endpoint:

```python
@router.get("/id/{match_id}/with-details/", response_model=MatchWithDetailsSchema)
async def get_match_with_details_endpoint(match_id: int):
    match = await self.service.get_match_with_details(match_id)
    return MatchWithDetailsSchema.model_validate(match)
```

## Team With Details

```python
@router.get("/id/{team_id}/with-details/", response_model=TeamWithDetailsSchema)
async def get_team_with_details_endpoint(team_id: int):
    team = await self.service.get_team_with_details(team_id)
    return TeamWithDetailsSchema.model_validate(team)
```

## Paginated With Details

```python
class PaginatedTeamWithDetailsResponse(BaseModel):
    data: list[TeamWithDetailsSchema]
    metadata: PaginationMetadata
```
