# Migration Plan

## Steps

1. Inventory all schema files and list missing schema tiers
2. Align naming conventions per standard
3. Add `SchemaUpdate` via `make_fields_optional()` where missing
4. Ensure all output schemas use `ConfigDict(from_attributes=True)`
5. Add missing `WithDetails` / `WithFullDetails` variants
6. Update routers to use consistent response models
7. Add/extend tests for schema validation

## Migration Notes

- Prefer additive changes to avoid breaking clients
- Add new schemas before removing old names
- Update references in docs and routers incrementally
