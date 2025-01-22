# Utility function to create and return a database entity
async def create_test_entity(factory, test_db):
    """Generic utility function to create and return a database entity."""
    entity = factory.build()
    async with test_db.async_session() as session:
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
    return entity
