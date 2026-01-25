# pg_trgm Search Optimization Guide

This guide documents the implementation of PostgreSQL's `pg_trgm` extension for optimized ILIKE-based search in Statsboard backend.

## Overview

The `pg_trgm` (trigram) extension provides trigram-based substring matching with GIN indexes, enabling fast indexed lookups for ILIKE queries with patterns like `%text%` (middle-of-text search).

## Search Approach

The project uses **ILIKE with ICU collation** as the primary search method:
- **ILIKE**: Case-insensitive pattern matching
- **ICU collation** (`en-US-x-icu`): Proper international text handling for Cyrillic, Latin, and Unicode scripts
- **pg_trgm indexes**: Optional performance optimization for large datasets

This approach is simpler than full-text search (tsvector) while still providing:
- Fast substring matching
- International language support
- Simple implementation pattern

### Benefits

- **Substring matching anywhere** in text (not just prefixes)
- **Fast indexed lookups** using trigram-based GIN indexes
- **Backward compatibility** with ILIKE operator semantics
- **International text support** when combined with ICU collation

### Performance

- **Expected improvement**: 100-1800x on large datasets (based on PostgreSQL benchmarks)
- **Target**: < 50ms for typical search queries on large datasets
- **Small datasets**: Sequential scan may still be used (faster than index overhead)

### Trade-offs

- **Index size**: GIN indexes with pg_trgm are larger than standard B-Tree indexes (~3-4x)
- **Write performance**: Slightly slower INSERT/UPDATE due to trigram index maintenance
- **Short queries**: Search terms < 3 characters may not benefit significantly

## Implementation Pattern

### 1. Database Migration

Create a migration to install the extension and create GIN indexes:

```python
# alembic/versions/YYYY_MM_DD_HHMM-{hash}_add_pg_trgm_extension_for_{domain}.py

def upgrade() -> None:
    # Install pg_trgm extension
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    # Create GIN indexes with gin_trgm_ops for ILIKE support
    op.execute("""
        CREATE INDEX ix_{table}_{field}_trgm
        ON {table} USING GIN ({field} gin_trgm_ops);
    """)

def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS ix_{table}_{field}_trgm;
    """)

    op.execute("""
        DROP EXTENSION IF EXISTS pg_trgm;
    """)
```

**Key points**:
- Use `gin_trgm_ops` operator class for ILIKE support
- Create separate indexes for each searchable field
- Include proper rollback in downgrade()

### 2. Model Updates

No model changes required for pg_trgm (unlike tsvector columns for full-text search).

### 3. Service Layer Implementation

The search implementation uses ILIKE with ICU collation for international text support:

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

    async with self.db.get_session_maker()() as session:
        base_query = select({Model}DB)

        # Search pattern matching with ICU collation for international text
        if search_query:
            search_pattern = f"%{search_query}%"
            base_query = base_query.where(
                {Model}DB.field.ilike(search_pattern).collate("en-US-x-icu")
                | {Model}DB.field2.ilike(search_pattern).collate("en-US-x-icu")
            )

        # Pagination and ordering logic...
```

**Key points**:
- Use `ilike()` with `.collate("en-US-x-icu")` for proper international text handling
- Search pattern `%query%` matches substring anywhere in text
- pg_trgm indexes accelerate ILIKE queries automatically when beneficial

### 4. Test Database Setup

Ensure pg_trgm is installed in test database fixtures:

```python
# tests/conftest.py

@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Database fixture that ensures a clean state using transactions."""
    db_url_str = str(db_url)
    database = Database(db_url_str, echo=False)

    # ... existing setup ...

    # Create tables at start of each test (faster than migrations)
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Install pg_trgm extension for search optimization tests
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

        # Create GIN indexes for search optimization
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_{table}_{field}_trgm
            ON {table} USING GIN ({field} gin_trgm_ops)
        """))
```

**Key points**:
- Install extension in test fixture to avoid migration dependency
- Create indexes after `create_all()` to ensure tables exist
- Use `IF NOT EXISTS` for idempotent fixture execution

## When to Use pg_trgm

### pg_trgm (Trigram Index for ILIKE)

**Use when**:
- Need substring matching anywhere in text
- Search patterns like `%text%` (not just prefixes)
- Want ILIKE compatibility (case-insensitive)
- Have large datasets (> 1000 rows)

**Best for**:
- Person names, place names, titles
- Multi-language text with Unicode
- Autocomplete suggestions

**Avoid when**:
- Search terms are always < 3 characters (trigrams ineffective)
- Exact match is sufficient (= or IN)
- Prefix-only search is needed (standard B-Tree index is smaller)
- Have small datasets (< 1000 rows)

### B-Tree Indexes (Alternative)

**Use when**:
- Search is always prefix-based (text%)
- Need exact equality matches (=)
- Have small datasets (< 1000 rows)
- Index size is critical (storage-constrained)

**Best for**:
- IDs, codes, structured identifiers
- Prefix-only search
- Small lookup tables

**Note**: The project previously used `tsvector` for full-text search but migrated to ILIKE for simpler implementation with equivalent functionality for use cases like person/team name search.

## Performance Considerations

### Index Usage

PostgreSQL query planner decides whether to use GIN indexes based on:
- **Dataset size**: Small datasets may use sequential scan (faster)
- **Selectivity**: Queries matching many rows may prefer sequential scan
- **Statistics**: Need accurate statistics (`ANALYZE` after bulk loads)

**Check index usage**:
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM person WHERE first_name ILIKE '%query%';
```

- Look for `Bitmap Index Scan` or `Bitmap Heap Scan`
- `Seq Scan` indicates index not used (expected for small datasets)

### Bulk Operations

After bulk inserts/updates:
```sql
-- Update table statistics
ANALYZE {table};
```

This helps query planner make better decisions about index usage.

### Index Size Monitoring

Monitor index size growth:
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid::regclass) AS size
FROM pg_stat_user_indexes
WHERE indexname LIKE '%trgm%';
```

GIN indexes are typically 3-4x larger than B-Tree indexes.

## Example Implementation

### Person Domain

See `src/person/` for complete implementation:
- **Service**: `PersonServiceDB.search_persons_with_pagination()` in `src/person/db_services.py`
- **Benchmarks**: `TestPersonSearchPerformance` in `tests/test_benchmarks.py`

### Team Domain

See `src/teams/` for complete implementation:
- **Service**: `TeamServiceDB.search_teams_with_pagination()` in `src/teams/db_services.py`

### Indexed Fields

- `first_name`: GIN index with `gin_trgm_ops`
- `second_name`: GIN index with `gin_trgm_ops`

### Search Capabilities

- **Substring matching**: "ала" matches "Алабин", "Малахов", "Паламарчук"
- **Case-insensitive**: "alice" matches "Alice", "ALICE"
- **Multi-language**: Works with Cyrillic, Latin, and other Unicode scripts
- **Middle-of-text**: "rist" matches "Christopher" (not just prefix)

## Extending to Other Domains

Follow this pattern to add pg_trgm to other domains:

1. **Create migration**:
   ```bash
   alembic revision -m "add pg_trgm for {domain} search"
   ```

2. **Define indexes**:
   ```python
   op.execute("""
       CREATE INDEX ix_{table}_{field}_trgm
       ON {table} USING GIN ({field} gin_trgm_ops);
   """)
   ```

3. **Implement search**:
   ```python
   search_pattern = f"%{search_query}%"
   base_query = base_query.where(
       Model.field.ilike(search_pattern).collate("en-US-x-icu")
   )
   ```

4. **Update test fixtures**:
   ```python
   await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
   await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_{table}_{field}_trgm..."))
   ```

5. **Add benchmarks**:
   ```python
   @pytest.mark.benchmark
   @pytest.mark.asyncio
   class Test{Domain}SearchPerformance:
       async def test_search_{domain}_by_name(...):
   ```

6. **Run tests**:
   ```bash
   pytest tests/test_benchmarks.py::Test{Domain}SearchPerformance -n 0
   ```

## Troubleshooting

### Index Not Used in EXPLAIN

**Problem**: Sequential scan used instead of GIN index

**Causes**:
- Dataset too small (planner prefers seq scan)
- Table statistics outdated (`ANALYZE` needed)
- Index not compatible with query (wrong operator class)

**Solutions**:
- Run `ANALYZE {table}` after bulk loads
- Verify index created with `gin_trgm_ops`
- Check dataset size (indexes may not help for < 100 rows)

### Poor Search Performance

**Problem**: Search slower than expected

**Causes**:
- Indexes not created or corrupted
- ICU collation conflicts with pg_trgm
- Connection pooling issues (new connections don't see indexes)

**Solutions**:
- Verify extension: `SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'`
- Check indexes: `SELECT indexname FROM pg_indexes WHERE indexname LIKE '%trgm%'`
- Test without collation (temporary) to isolate issue

### International Text Issues

**Problem**: Cyrillic/Unicode search not working

**Causes**:
- Missing ICU collation
- Wrong collation specified
- Database locale not configured for Unicode

**Solutions**:
- Use `.collate("en-US-x-icu")` on ILIKE expressions
- Verify ICU extension installed: `SELECT extname FROM pg_extension WHERE extname = 'icu'`
- Check database collation: `SHOW LC_COLLATE;`

## References

- **PostgreSQL pg_trgm docs**: https://www.postgresql.org/docs/current/pgtrgm.html
- **GIN Indexes**: https://www.postgresql.org/docs/current/gin.html
- **ILIKE operators**: https://www.postgresql.org/docs/current/functions-matching.html

## Related Files

- `src/person/db_services.py` - Search implementation
- `src/teams/db_services.py` - Search implementation
- `tests/conftest.py` - Test database setup (pg_trgm indexes)
- `tests/test_benchmarks.py` - Performance benchmarks
- `AGENTS.md` - Search implementation guide
