import pytest

from src.sponsor_lines.db_services import SponsorLineServiceDB
from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB
from src.sponsor_sponsor_line_connection.schemas import SponsorSponsorLineSchemaCreate
from src.sponsors.db_services import SponsorServiceDB
from tests.factories import SponsorFactory, SponsorLineFactory



@pytest.mark.asyncio
class TestSponsorSponsorLineServiceDB:
    async def test_create_sponsor_sponsor_line(self, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        connection_service = SponsorSponsorLineServiceDB(test_db)
        connection_data = SponsorSponsorLineSchemaCreate(
            sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id, position=1
        )

        result = await connection_service.create(connection_data)

        assert result is not None
        assert result.id is not None
        assert result.sponsor_id == sponsor.id

    async def test_create_duplicate_sponsor_sponsor_line(self, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        connection_service = SponsorSponsorLineServiceDB(test_db)
        connection_data = SponsorSponsorLineSchemaCreate(
            sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id, position=1
        )

        result1 = await connection_service.create(connection_data)
        result2 = await connection_service.create(connection_data)

        assert result1 is not None
        assert result2 is None

    async def test_get_sponsor_sponsor_line_relation(self, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        connection_service = SponsorSponsorLineServiceDB(test_db)
        connection_data = SponsorSponsorLineSchemaCreate(
            sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id, position=1
        )

        created = await connection_service.create(connection_data)
        result = await connection_service.get_sponsor_sponsor_line_relation(
            sponsor.id, sponsor_line.id
        )

        assert result is not None
        assert result.id == created.id

    async def test_get_related_sponsors(self, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor1 = await sponsor_service.create(SponsorFactory.build(title="Sponsor 1"))
        sponsor2 = await sponsor_service.create(SponsorFactory.build(title="Sponsor 2"))

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        connection_service = SponsorSponsorLineServiceDB(test_db)
        await connection_service.create(
            SponsorSponsorLineSchemaCreate(
                sponsor_id=sponsor1.id, sponsor_line_id=sponsor_line.id, position=1
            )
        )
        await connection_service.create(
            SponsorSponsorLineSchemaCreate(
                sponsor_id=sponsor2.id, sponsor_line_id=sponsor_line.id, position=2
            )
        )

        result = await connection_service.get_related_sponsors(sponsor_line.id)

        assert result is not None
        assert "sponsors" in result
        assert len(result["sponsors"]) == 2

    async def test_delete_relation_by_sponsor_and_sponsor_line_id(self, test_db):
        from fastapi import HTTPException

        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        connection_service = SponsorSponsorLineServiceDB(test_db)
        await connection_service.create(
            SponsorSponsorLineSchemaCreate(
                sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id, position=1
            )
        )

        deleted_item = (
            await connection_service.delete_relation_by_sponsor_and_sponsor_line_id(
                sponsor.id, sponsor_line.id
            )
        )

        assert deleted_item is not None
        assert deleted_item.sponsor_id == sponsor.id
        assert deleted_item.sponsor_line_id == sponsor_line.id

        with pytest.raises(HTTPException) as exc_info:
            await connection_service.delete_relation_by_sponsor_and_sponsor_line_id(
                sponsor.id, sponsor_line.id
            )

        assert exc_info.value.status_code == 404

    async def test_delete_relation_not_found(self, test_db):
        from fastapi import HTTPException

        connection_service = SponsorSponsorLineServiceDB(test_db)

        with pytest.raises(HTTPException) as exc_info:
            await connection_service.delete_relation_by_sponsor_and_sponsor_line_id(
                99999, 99999
            )

        assert exc_info.value.status_code == 404
