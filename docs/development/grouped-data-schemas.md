# Grouped Data Schemas and Career Endpoint Pattern

## Overview

Use grouped data schemas when endpoints return pre-grouped historical data (player careers, event histories). The backend owns grouping logic to keep clients simple and consistent.

## Pattern Components

### 1. Base Assignment Schema

```python
class TeamAssignmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int | None = None
    team_title: str | None = None
    position_id: int | None = None
    position_title: str | None = None
    player_number: str | None = None
    tournament_id: int | None = None
    tournament_title: str | None = None
    season_id: int | None = None
    season_year: int | None = None
```

### 2. Grouped Container Schemas

```python
class CareerByTeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int | None = None
    team_title: str | None = None
    assignments: list[TeamAssignmentSchema] = Field(default_factory=list)


class CareerByTournamentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tournament_id: int | None = None
    tournament_title: str | None = None
    season_id: int | None = None
    season_year: int | None = None
    assignments: list[TeamAssignmentSchema] = Field(default_factory=list)
```

### 3. Response Schema

```python
class PlayerCareerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    career_by_team: list[CareerByTeamSchema] = Field(default_factory=list)
    career_by_tournament: list[CareerByTournamentSchema] = Field(default_factory=list)
```

## Service Layer Implementation

### Optimized Query with Eager Loading

```python
@handle_service_exceptions(item_name=ITEM, operation="fetching player career data")
async def get_player_career(self, player_id: int) -> PlayerCareerResponseSchema:
    async with self.db.get_session_maker()() as session:
        stmt = (
            select(PlayerDB)
            .options(
                selectinload(PlayerDB.person),
                selectinload(PlayerDB.player_team_tournament).selectinload(
                    PlayerTeamTournamentDB.team
                ),
                selectinload(PlayerDB.player_team_tournament).selectinload(
                    PlayerTeamTournamentDB.position
                ),
                selectinload(PlayerDB.player_team_tournament).selectinload(
                    PlayerTeamTournamentDB.tournament
                ).selectinload(TournamentDB.season),
            )
            .where(PlayerDB.id == player_id)
        )

        result = await session.execute(stmt)
        player = result.scalars().one_or_none()
        if not player:
            raise HTTPException(status_code=404, detail=f"Player id:{player_id} not found")
```

### Dictionary-Based Grouping Pattern

```python
assignments = [
    TeamAssignmentSchema(
        id=ptt.id,
        team_id=ptt.team_id,
        team_title=ptt.team.title if ptt.team else None,
        position_id=ptt.position_id,
        position_title=ptt.position.title if ptt.position else None,
        player_number=ptt.player_number,
        tournament_id=ptt.tournament_id,
        tournament_title=ptt.tournament.title if ptt.tournament else None,
        season_id=ptt.tournament.season_id if ptt.tournament else None,
        season_year=ptt.tournament.season.year if ptt.tournament and ptt.tournament.season else None,
    )
    for ptt in player.player_team_tournament
]

career_by_team_dict: dict[int | None, list[TeamAssignmentSchema]] = {}
for assignment in assignments:
    team_id = assignment.team_id
    if team_id not in career_by_team_dict:
        career_by_team_dict[team_id] = []
    career_by_team_dict[team_id].append(assignment)

career_by_tournament_dict: dict[tuple[int | None, int | None], list[TeamAssignmentSchema]] = {}
for assignment in assignments:
    key = (assignment.tournament_id, assignment.season_id)
    if key not in career_by_tournament_dict:
        career_by_tournament_dict[key] = []
    career_by_tournament_dict[key].append(assignment)
```

## Router Layer Implementation

```python
@router.get("/id/{player_id}/career", response_model=PlayerCareerResponseSchema)
async def player_career_endpoint(player_id: int):
    try:
        return await self.service.get_player_career(player_id)
    except HTTPException:
        raise
    except Exception as ex:
        self.logger.error(
            f"Error getting player career for player_id:{player_id} {ex}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error fetching player career",
        ) from ex
```

## Key Implementation Details

1. Single query with nested `selectinload()`
2. Dictionary-based grouping
3. Response sorting
4. 404 handling

## When to Use This Pattern

Use when:

- Frontend needs multiple views of the same historical data
- Grouping logic is complex or error-prone
- Backend can optimize queries better than frontend

Avoid when:

- Data is flat and ungrouped
- Grouping is dynamic based on user input

## Example Response

```json
{
  "career_by_team": [
    {
      "team_id": 1,
      "team_title": "FC Barcelona",
      "assignments": [
        {
          "id": 101,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ],
  "career_by_tournament": [
    {
      "tournament_id": 5,
      "tournament_title": "La Liga 2024",
      "season_id": 2,
      "season_year": 2024,
      "assignments": [
        {
          "id": 101,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ]
}
```
