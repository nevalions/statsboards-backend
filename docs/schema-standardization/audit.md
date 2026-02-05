# Audit

## Current State Analysis

Existing patterns in use:

| Schema Type | Purpose | Examples |
|--------------|---------|----------|
| `*SchemaBase` | Base fields shared across schemas | `PersonSchemaBase`, `TeamSchemaBase` |
| `*SchemaCreate` | POST input validation | `PersonSchemaCreate`, `TeamSchemaCreate` |
| `*SchemaUpdate` | PATCH/PUT input | Generated via `make_fields_optional()` |
| `*Schema` | Full response with id | `PersonSchema`, `MatchSchema` |
| `*WithDetailsSchema` | Nested relationships (1-2 levels) | `PlayerWithDetailsSchema` |
| `*WithFullDetailsSchema` | Deep relationships (3+ levels) | `PlayerWithFullDetailsSchema` |
| `*WithTitlesSchema` | Flattened title fields | `PlayerTeamTournamentWithTitles` |

## Domain Examples

### Player

```python
PlayerSchemaBase(PrivacyFieldsBase)
PlayerSchemaCreate(PlayerSchemaBase)
PlayerSchema(PlayerSchemaCreate)

PlayerWithDetailsSchema(PlayerSchema)
PlayerWithFullDetailsSchema(PlayerSchema)
```

### Team

```python
TeamSchemaBase(SponsorFieldsBase, PrivacyFieldsBase)
TeamSchemaCreate(TeamSchemaBase)
TeamSchema(TeamSchemaCreate)

TeamWithDetailsSchema(TeamSchema)
```

### Match

```python
MatchSchemaBase(SponsorFieldsBase, PrivacyFieldsBase)
MatchSchemaCreate(MatchSchemaBase)
MatchSchema(MatchSchemaCreate)

MatchWithDetailsSchema(MatchSchema)
```

### Tournament

```python
TournamentSchemaBase(SponsorFieldsBase, PrivacyFieldsBase)
TournamentSchemaCreate(TournamentSchemaBase)
TournamentSchema(TournamentSchemaCreate)

TournamentWithDetailsSchema(TournamentSchema)
```
