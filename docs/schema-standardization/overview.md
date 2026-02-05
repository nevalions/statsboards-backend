# Overview

This plan standardizes Pydantic schema patterns across the codebase. Goals:

- Consistent naming conventions
- Predictable schema hierarchies
- Clear guidance on nested vs flat schemas
- Easier onboarding and maintenance

Current patterns already present:

- `*SchemaBase`, `*SchemaCreate`, `*SchemaUpdate`, `*Schema`
- `*WithDetailsSchema`, `*WithFullDetailsSchema`, `*WithTitlesSchema`

Shared base schemas in `src/core/shared_schemas.py` include:

- `SponsorFieldsBase`
- `PrivacyFieldsBase`
- `LogoFieldsBase`
- `PlayerTeamTournamentBaseFields`
- `PlayerTeamTournamentWithTitles`
