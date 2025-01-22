# # Utility function to create and return a database entity
# async def create_test_entity(factory, test_db):
#     """Generic utility function to create and return a database entity."""
#     print(factory)
#     entity = factory.build()
#     async with test_db.async_session() as session:
#         session.add(entity)
#         await session.commit()
#         await session.refresh(entity)
#     return entity
async def create_test_entity(factory, test_db):
    """Generic utility function to create and return a database entity."""
    # Make sure we're using create() here on the factory
    print(f"Creating entity using factory: {factory}")

    # Correct way to use create() on the factory
    entity = factory.create()  # This ensures it's added to the DB

    async with test_db.async_session() as session:
        print(f"Adding entity {entity} to DB session")
        session.add(entity)
        await session.commit()  # Ensure commit is called
        await session.refresh(entity)  # Refresh to get the ID
    print(f"Entity {entity} after commit: {entity.id}")
    return entity
