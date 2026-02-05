# Overview

Combined schemas are Pydantic schemas that embed related entities for richer responses (e.g., match with teams and tournament).

Use them when the frontend needs a single payload with nested data and when service methods can efficiently eager-load relationships.

See `docs/schemas/patterns.md` for implementation patterns and `docs/schemas/examples.md` for concrete examples.
