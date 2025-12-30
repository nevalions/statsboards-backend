import asyncio
import time
from sqlalchemy import select, text
from src.core.models import PlayerMatchDB, FootballEventDB, ScoreboardDB, PlayerTeamTournamentDB, MatchDB
from src.core.models.base import Database


async def measure_query_performance(db: Database, query_name: str, query):
    """Measure execution time of a query"""
    start_time = time.time()
    async with db.async_session() as session:
        result = await session.execute(query)
        rows = result.all()
        end_time = time.time()
    return {
        "query": query_name,
        "rows": len(rows),
        "time_ms": round((end_time - start_time) * 1000, 2)
    }


async def check_index_exists(db: Database, table_name: str, index_name: str):
    """Check if an index exists"""
    async with db.async_session() as session:
        query = text("""
            SELECT COUNT(*) as count
            FROM pg_indexes
            WHERE tablename = :table_name
            AND indexname = :index_name
        """)
        result = await session.execute(query, {"table_name": table_name, "index_name": index_name})
        count = result.scalar()
        return count > 0


async def get_table_stats(db: Database, table_name: str):
    """Get row count for a table"""
    async with db.async_session() as session:
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = await session.execute(query)
        return result.scalar()


async def main():
    """Main function to measure query performance"""
    db_url = "postgresql+asyncpg://stats:ZenitStats@92.255.79.85:5444/statsdev"
    db = Database(db_url, echo=False)
    
    print("=" * 60)
    print("DATABASE PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Get table sizes
    print("\n1. TABLE ROW COUNTS")
    print("-" * 60)
    tables = {
        "player_match": PlayerMatchDB,
        "football_event": FootballEventDB,
        "scoreboard": ScoreboardDB,
        "player_team_tournament": PlayerTeamTournamentDB,
        "match": MatchDB,
    }
    
    for table_name, model in tables.items():
        count = await get_table_stats(db, table_name)
        print(f"  {table_name}: {count:,} rows")
    
    # Check if indexes exist
    print("\n2. EXISTING INDEXES CHECK")
    print("-" * 60)
    indexes = [
        ("player_match", "ix_player_match_match_id_player_match_eesl_id"),
        ("football_event", "ix_football_event_match_id"),
        ("scoreboard", "ix_scoreboard_match_id_player_match_lower_id"),
        ("player_team_tournament", "ix_player_team_tournament_tournament_id_player_id"),
        ("match", "ix_match_tournament_id_team_a_id_team_b_id"),
    ]
    
    for table_name, index_name in indexes:
        exists = await check_index_exists(db, table_name, index_name)
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {index_name}: {status}")
    
    # Measure query performance
    print("\n3. QUERY PERFORMANCE (before indexes)")
    print("-" * 60)
    
    # Get a sample match_id that has data in all tables
    async with db.async_session() as session:
        result = await session.execute(select(MatchDB).limit(1))
        sample_match = result.scalar_one_or_none()
        sample_match_id = sample_match.id if sample_match else None
        sample_tournament_id = sample_match.tournament_id if sample_match else None
        sample_team_a_id = sample_match.team_a_id if sample_match else None
        sample_team_b_id = sample_match.team_b_id if sample_match else None
        
        result = await session.execute(
            select(PlayerTeamTournamentDB).where(PlayerTeamTournamentDB.tournament_id == sample_tournament_id).limit(1)
        )
        sample_ptt = result.scalar_one_or_none()
        sample_player_id = sample_ptt.player_id if sample_ptt else None
        
        result = await session.execute(
            select(PlayerMatchDB).where(PlayerMatchDB.match_id == sample_match_id).limit(1)
        )
        sample_pm = result.scalar_one_or_none()
        sample_player_match_eesl_id = sample_pm.player_match_eesl_id if sample_pm else None
        sample_player_match_lower_id = sample_pm.id if sample_pm else None
    
    if sample_match_id:
        # player_match query
        query1 = select(PlayerMatchDB).where(
            PlayerMatchDB.match_id == sample_match_id,
            PlayerMatchDB.player_match_eesl_id == sample_player_match_eesl_id
        )
        result1 = await measure_query_performance(
            db,
            "player_match: (match_id, player_match_eesl_id)",
            query1
        )
        print(f"  {result1['query']}: {result1['time_ms']}ms ({result1['rows']} rows)")
        
        # football_event query
        query2 = select(FootballEventDB).where(FootballEventDB.match_id == sample_match_id)
        result2 = await measure_query_performance(
            db,
            "football_event: (match_id)",
            query2
        )
        print(f"  {result2['query']}: {result2['time_ms']}ms ({result2['rows']} rows)")
        
        # scoreboard query
        query3 = select(ScoreboardDB).where(
            ScoreboardDB.match_id == sample_match_id,
            ScoreboardDB.player_match_lower_id == sample_player_match_lower_id
        )
        result3 = await measure_query_performance(
            db,
            "scoreboard: (match_id, player_match_lower_id)",
            query3
        )
        print(f"  {result3['query']}: {result3['time_ms']}ms ({result3['rows']} rows)")
    
    if sample_tournament_id and sample_player_id:
        # player_team_tournament query
        query4 = select(PlayerTeamTournamentDB).where(
            PlayerTeamTournamentDB.tournament_id == sample_tournament_id,
            PlayerTeamTournamentDB.player_id == sample_player_id
        )
        result4 = await measure_query_performance(
            db,
            "player_team_tournament: (tournament_id, player_id)",
            query4
        )
        print(f"  {result4['query']}: {result4['time_ms']}ms ({result4['rows']} rows)")
    
    if sample_tournament_id and sample_team_a_id and sample_team_b_id:
        # match query
        query5 = select(MatchDB).where(
            MatchDB.tournament_id == sample_tournament_id,
            MatchDB.team_a_id == sample_team_a_id,
            MatchDB.team_b_id == sample_team_b_id
        )
        result5 = await measure_query_performance(
            db,
            "match: (tournament_id, team_a_id, team_b_id)",
            query5
        )
        print(f"  {result5['query']}: {result5['time_ms']}ms ({result5['rows']} rows)")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
