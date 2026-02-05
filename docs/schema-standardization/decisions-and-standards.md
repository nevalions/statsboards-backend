# Decisions and Standards

## Naming Conventions

`{Entity}{Purpose}` where Purpose is one of:

- `SchemaBase`
- `SchemaCreate`
- `SchemaUpdate`
- `Schema`
- `WithDetailsSchema`
- `WithFullDetailsSchema`
- `WithTitlesSchema`
- `{Entity}ListItemSchema`

## Schema Hierarchy Rules

Every domain with relationships must include:

1. Base schema (`{Entity}SchemaBase`)
2. Create schema (`{Entity}SchemaCreate`)
3. Update schema (`{Entity}SchemaUpdate` using `make_fields_optional()`)
4. Response schema (`{Entity}Schema`)

## Nested vs Flat

- `WithDetailsSchema`: 1-2 levels of relationships
- `WithFullDetailsSchema`: 3+ levels of relationships
- `WithTitlesSchema`: flattened titles for display

## Field Requirements

- Use `Field()` with descriptions and examples
- Use `Annotated` constraints where appropriate
- Output schemas set `model_config = ConfigDict(from_attributes=True)`
