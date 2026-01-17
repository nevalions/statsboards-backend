# Database Migration Anti-Patterns

This document catalogs common anti-patterns encountered in database migrations, with real-world examples and solutions.

## Dropping Columns Without Cleaning Up Dependent Objects

### Problem
When dropping database columns, you must also remove all dependent database objects such as triggers, functions, views, and indexes that reference those columns.

### Real-World Example: search_vector Trigger Error

**Migration:** `2026_01_15_1358-935b31e992ed_add_iscurrent_field_to_season_model.py`

This migration dropped `search_vector` columns from three tables:
- `player_team_tournament.search_vector`
- `person.search_vector`
- `team.search_vector`

However, it only dropped the **indexes** but left behind **triggers** and **functions** that referenced these columns:

```sql
-- Orphaned trigger still existed:
CREATE TRIGGER player_team_tournament_search_vector_trigger 
BEFORE INSERT OR UPDATE OF player_number, player_id 
ON player_team_tournament 
FOR EACH ROW 
EXECUTE FUNCTION player_team_tournament_search_vector_update()

-- Trigger function referenced dropped column:
CREATE FUNCTION player_team_tournament_search_vector_update()
RETURNS trigger AS $function$
BEGIN
    NEW.search_vector :=  -- ❌ search_vector column no longer exists!
        to_tsvector('simple', COALESCE(NEW.player_number, '')) || 
        to_tsvector('simple', COALESCE(
            SELECT COALESCE(first_name, '') || ' ' || COALESCE(second_name, '')
            FROM player WHERE player.id = player_team_tournament.player_id
        ), ''));
    RETURN NEW;
END;
$function$
```

**Error Observed:**
```
asyncpg.exceptions.UndefinedColumnError: record "new" has no field "search_vector"
[SQL: UPDATE player_team_tournament SET player_number=$1::VARCHAR WHERE player_team_tournament.id = $2::INTEGER]
```

### Root Cause

The migration only removed the column and indexes but forgot to:
1. Drop triggers that referenced the column
2. Drop trigger functions that set values for the column

### Solution

**Migration:** `2026_01_17_2317-a5855ca979f4_drop_search_vector_triggers_and_.py`

```python
def upgrade() -> None:
    # Drop triggers first (CASCADE handles dependent functions)
    op.execute("DROP TRIGGER IF EXISTS player_team_tournament_search_vector_trigger ON player_team_tournament CASCADE")
    op.execute("DROP TRIGGER IF EXISTS person_search_vector_trigger ON person CASCADE")
    op.execute("DROP TRIGGER IF EXISTS team_search_vector_trigger ON team CASCADE")
```

**Key points:**
- Use `CASCADE` to automatically drop dependent functions
- Drop triggers before dropping columns in the same migration if possible
- Always check for dependent objects before dropping columns

### Prevention Checklist

Before dropping a column, always check for:

1. **Triggers:**
   ```sql
   SELECT tgname, tgrelid::regclass 
   FROM pg_trigger 
   WHERE tgrelid = 'your_table'::regclass;
   ```

2. **Functions that reference the column:**
   ```sql
   SELECT proname, pg_get_functiondef(oid) 
   FROM pg_proc 
   WHERE pg_get_functiondef(oid) LIKE '%your_column_name%';
   ```

3. **Views:**
   ```sql
   SELECT viewname, definition 
   FROM pg_views 
   WHERE definition LIKE '%your_column_name%';
   ```

4. **Indexes:**
   ```sql
   SELECT indexname, indexdef 
   FROM pg_indexes 
   WHERE tablename = 'your_table' 
   AND indexdef LIKE '%your_column_name%';
   ```

### Best Practice: Cleanup in Single Migration

When possible, remove dependent objects **in the same migration** that drops the column:

```python
def upgrade() -> None:
    # 1. Drop triggers that use the column
    op.execute("DROP TRIGGER IF EXISTS ... ON your_table CASCADE")
    
    # 2. Drop indexes that use the column
    op.drop_index("ix_your_column", table_name="your_table")
    
    # 3. Drop the column
    op.drop_column("your_table", "your_column")
```

### Detection Strategies

1. **Test in development first** - run migrations against a copy of production data
2. **Check for errors on next write operation** - triggers fire on INSERT/UPDATE, so test these operations
3. **Review migration logs** - look for warnings about dependent objects
4. **Use schema comparison tools** - compare dev vs prod schema after migrations

### Related Anti-Patterns

- **Leaving orphaned indexes:** Dropping columns without removing indexes that reference them
- **Incomplete CASCADE deletions:** Not using CASCADE when dropping objects with dependents
- **Assumption of ownership:** Assuming dropping a table automatically cleans up all triggers (it does in some DBs, but explicit is safer)

### References

- PostgreSQL: `DROP TRIGGER` documentation
- PostgreSQL: `DROP FUNCTION` documentation
- Alembic: `op.execute()` for raw SQL
