# PostgreSQL pg_trgm Search Optimization Pattern

This document describes the pattern for implementing PostgreSQL `pg_trgm` extension to accelerate ILIKE-based middle-of-text searches across multiple domains.

## Overview

PostgreSQL's `pg_trgm` extension provides **trigram-based substring matching** with **GIN indexes** that can significantly accelerate ILIKE queries containing leading/trailing wildcards (`%query%`). This is particularly useful for search functionality where users can search anywhere within text fields.

### Performance Improvements

Based on research and testing:
- **100-1800x improvement** on search queries vs. full table scans
- Typical search time reduced from ~1000ms to <50ms
- Effective for search terms >= 3 characters

### How It Works

1. **Trigrams**: Text is broken down into sequences of 3 consecutive characters
2. **GIN Index**: Stores trigrams for fast lookup
3. **ILIKE Acceleration**: PostgreSQL can use the GIN index for ILIKE queries with `%query%` patterns

## Implementation Pattern

### Step 1: Create Alembic Migration

Create a new migration file to install the extension and create indexes:

```python
"""add pg_trgm extension for {table_name} search optimization

Revision ID: {timestamp}-{hash}
Revises: {previous_revision_id}
Create Date: YYYY-MM-DD HH:MM:SS

"""

from alembic import op


def upgrade() -> None:
    # Install pg_trgm extension (idempotent - safe to run multiple times)
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    # Create GIN indexes on text fields with gin_trgm_ops operator class
    # Important: gin_trgm_ops is required for ILIKE pattern matching
    op.execute(f"""
        CREATE INDEX ix_{table_name}_{column_name}_gin_trgm
        ON {table_name} USING GIN ({column_name} gin_trgm_ops);
    """)

    # Repeat for additional columns as needed
    op.execute(f"""
        CREATE INDEX ix_{table_name}_{other_column}_gin_trgm
        ON {table_name} USING GIN ({other_column} gin_trgm_ops);
    """)


def downgrade() -> None:
    # Drop indexes (reverse order)
    op.execute(f"""
        DROP INDEX IF EXISTS ix_{table_name}_{other_column}_gin_trgm;
    """)

    op.execute(f"""
        DROP INDEX IF EXISTS ix_{table_name}_{column_name}_gin_trgm;
    """)

    # Drop extension (optional - only if no other domains use it)
    op.execute("""
        DROP EXTENSION IF EXISTS pg_trgm;
    """)
```

### Step 2: Verify Search Implementation

Your search implementation should use ILIKE with pattern matching. **No code changes required** - the indexes automatically accelerate existing queries:

```python
# src/{domain}/db_services.py
async def search_{entity}s_with_pagination(
    self,
    search_query: str | None = None,
    skip: int = 0,
    limit: int = 20,
    order_by: str = "{default_field}",
    order_by_two: str = "id",
    ascending: bool = True,
) -> Paginated{Entity}Response:
    self.logger.debug(f"Search {ITEM}: query={search_query}")

    async with self.db.async_session() as session:
        base_query = select({Model}DB)

        # This ILIKE query will now use pg_trgm GIN indexes!
        if search_query:
            search_pattern = f"%{search_query}%"
            base_query = base_query.where(
                {Model}DB.field1.ilike(search_pattern)
                | {Model}DB.field2.ilike(search_pattern)
            )

        # ... rest of pagination logic
```

### Step 3: Add Performance Benchmarks

Create benchmark tests to validate performance improvement:

```python
# tests/test_benchmarks.py

@pytest.mark.benchmark
@pytest.mark.asyncio
class Test{Domain}SearchPerformance:
    """Benchmark tests for {Domain} search operations with pg_trgm optimization."""

    async def test_search_{domain}_by_name_short(self, test_{domain}_service, test_db, benchmark):
        """Benchmark search with short name (3 chars)."""
        from tests.factories import {Domain}Factory

        # Create test data
        for i in range(100):
            entity_data = {Domain}Factory.build(name=f"Test{i}")
            await test_{domain}_service.create(entity_data)

        async def search_short():
            return await test_{domain}_service.search_{domain}s_with_pagination(
                search_query="Tes",
                skip=0,
                limit=20,
            )

        result = await benchmark.pedantic(search_short)
        assert result.metadata.total_items > 0

    async def test_search_{domain}_middle_of_text(self, test_{domain}_service, test_db, benchmark):
        """Benchmark search with substring in middle of text."""
        from tests.factories import {Domain}Factory

        for i in range(100):
            entity_data = {Domain}Factory.build(name=f"Christopher{i}")
            await test_{domain}_service.create(entity_data)

        async def search_middle():
            return await test_{domain}_service.search_{domain}s_with_pagination(
                search_query="rist",
                skip=0,
                limit=20,
            )

        result = await benchmark.pedantic(search_middle)
        assert result.metadata.total_items > 0
```

Run benchmarks to establish baseline:

```bash
# Run benchmarks
pytest tests/test_benchmarks.py::Test{Domain}SearchPerformance -m benchmark

# Compare with baseline
pytest tests/test_benchmarks.py::Test{Domain}SearchPerformance -m benchmark --benchmark-compare
```

### Step 4: Apply Migration

Apply the migration to your database:

```bash
# Development database
source venv/bin/activate
alembic upgrade head

# Test database (for running benchmarks)
docker-compose -f docker-compose.test-db-only.yml up -d
source venv/bin/activate
TESTING=1 alembic upgrade head
```

## Best Practices

### When to Use pg_trgm

**Good candidates for pg_trgm:**
- Search functionality on text fields (names, titles, descriptions)
- ILIKE queries with leading/trailing wildcards (`%query%`)
- Fields frequently searched with varying substrings
- Tables with > 1000 records where full table scans are slow

**Poor candidates for pg_trgm:**
- Short text fields (< 3 chars) - trigrams require 3+ chars
- Fields only searched with exact matches or prefix searches (use B-Tree indexes instead)
- Tables with < 100 records where full table scans are already fast

### Index Size Considerations

**GIN indexes with pg_trgm are larger** than standard B-Tree indexes:
- Approximately **3-5x larger** than B-Tree on the same column
- Factor this into your storage planning
- Monitor index size after creation:

```sql
-- Check index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE indexname LIKE '%gin_trgm%'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

### Write Performance Impact

**Insert/UPDATE operations are slightly slower** due to trigram index maintenance:
- Typical overhead: 5-15% slower writes
- Consider this for write-heavy workloads
- Monitor query plan to ensure indexes are being used:

```sql
-- Check if pg_trgm indexes are used
EXPLAIN ANALYZE
SELECT * FROM person
WHERE first_name ILIKE '%query%';

-- Look for "Bitmap Index Scan" or "Index Scan using ix_person_first_name_gin_trgm"
```

### Minimum Search Term Length

**pg_trgm is most effective for search terms >= 3 characters:**
- 3+ chars: Good performance improvement
- 1-2 chars: Limited improvement (too few trigrams to match)
- Consider filtering UI to require 3+ chars for search

### ICU Collation Compatibility

**pg_trgm works with ICU collations** for international text:
- Continue using `.collate("en-US-x-icu")` in your queries
- Test thoroughly with non-ASCII characters in your specific language
- pg_trgm handles most international text, but edge cases exist

### Multiple Domains Sharing Extension

**The pg_trgm extension is database-level, not table-level:**
- Only install the extension once per database
- Multiple domains can use the same extension
- In `downgrade()`, only drop the extension if it's safe (no other tables using it)

```python
# In first migration to use pg_trgm
op.execute("""
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
""")

# In subsequent migrations (do NOT install extension again)
# Only create indexes:
op.execute(f"""
    CREATE INDEX ix_{table_name}_{column}_gin_trgm
    ON {table_name} USING GIN ({column} gin_trgm_ops);
""")
```

## Verification Checklist

After implementing pg_trgm for a domain:

- [ ] Migration created and applied successfully
- [ ] Indexes exist in database (`\di + {table_name}`)
- [ ] EXPLAIN ANALYZE shows index usage (not Seq Scan)
- [ ] Benchmarks show significant improvement (100-1800x)
- [ ] Search queries still return correct results
- [ ] International text (non-ASCII) works correctly
- [ ] Write performance impact is acceptable
- [ ] Index size is within storage budget

## Example: Person Domain

See the following files for a complete working example:

**Migration:** `alembic/versions/2026_01_06_1724-b228bf69e534_add_pg_trgm_extension_and_indexes_for_.py`

**Service:** `src/person/db_services.py` - search_persons_with_pagination() method

**Benchmarks:** `tests/test_benchmarks.py` - TestPersonSearchPerformance class

## Additional Resources

- [PostgreSQL pg_trgm Documentation](https://www.postgresql.org/docs/current/pgtrgm.html)
- [GIN Index Documentation](https://www.postgresql.org/docs/current/gin.html)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

## Migration Notes

### Before Applying pg_trgm

1. **Backup your database**
   ```bash
   pg_dump statsboards_db > backup_before_pg_trgm.sql
   ```

2. **Measure baseline performance**
   ```bash
   pytest tests/test_benchmarks.py::TestPersonSearchPerformance -m benchmark --benchmark-save=baseline
   ```

### After Applying pg_trgm

1. **Verify indexes are used**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM person WHERE first_name ILIKE '%Test%';
   ```

2. **Measure improvement**
   ```bash
   pytest tests/test_benchmarks.py::TestPersonSearchPerformance -m benchmark --benchmark-compare
   ```

3. **Monitor index size**
   ```sql
   SELECT pg_size_pretty(pg_total_relation_size('person'));
   ```

### Rollback if Needed

```bash
alembic downgrade -1
```

The migration includes safe `IF EXISTS` checks for all operations.
