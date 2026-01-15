import pytest

from src.sponsor_lines.db_services import SponsorLineServiceDB
from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB
from src.sponsor_sponsor_line_connection.schemas import (
    SponsorSponsorLineSchemaCreate,
    SponsorSponsorLineSchemaUpdate,
)
from src.sponsors.db_services import SponsorServiceDB
from tests.factories import SponsorFactory, SponsorLineFactory


@pytest.mark.asyncio
class TestSponsorSponsorLineViews:
    async def test_create_sponsor_sponsor_line_relation_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        response = await client.post(
            f"/api/sponsor_in_sponsor_line/{sponsor.id}in{sponsor_line.id}"
        )

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_sponsor_sponsor_line_relation_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        ssl_service = SponsorSponsorLineServiceDB(test_db)
        relation_data = SponsorSponsorLineSchemaCreate(
            sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id
        )
        created = await ssl_service.create(relation_data)

        response = await client.get(
            f"/api/sponsor_in_sponsor_line/{sponsor.id}in{sponsor_line.id}"
        )

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_sponsor_sponsor_line_relation_not_found(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        await sponsor_line_service.create(SponsorLineFactory.build())

        response = await client.get("/api/sponsor_in_sponsor_line/99999in99999")

        assert response.status_code == 404

    async def test_update_sponsor_sponsor_line_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        ssl_service = SponsorSponsorLineServiceDB(test_db)
        relation_data = SponsorSponsorLineSchemaCreate(
            sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id
        )
        created = await ssl_service.create(relation_data)

        update_data = SponsorSponsorLineSchemaUpdate(position=2)

        response = await client.put(
            f"/api/sponsor_in_sponsor_line/{created.id}/",
            json=update_data.model_dump(),
        )

        assert response.status_code == 200

    async def test_update_sponsor_sponsor_line_not_found(self, client):
        update_data = SponsorSponsorLineSchemaUpdate(position=2)

        response = await client.put(
            "/api/sponsor_in_sponsor_line/99999/",
            json=update_data.model_dump(),
        )

        assert response.status_code == 404

    async def test_get_sponsors_in_sponsor_line_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor1 = await sponsor_service.create(SponsorFactory.build(title="Sponsor 1"))
        sponsor2 = await sponsor_service.create(SponsorFactory.build(title="Sponsor 2"))

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        ssl_service = SponsorSponsorLineServiceDB(test_db)
        await ssl_service.create(
            SponsorSponsorLineSchemaCreate(
                sponsor_id=sponsor1.id, sponsor_line_id=sponsor_line.id
            )
        )
        await ssl_service.create(
            SponsorSponsorLineSchemaCreate(
                sponsor_id=sponsor2.id, sponsor_line_id=sponsor_line.id
            )
        )

        response = await client.get(
            f"/api/sponsor_in_sponsor_line/sponsor_line/id/{sponsor_line.id}/sponsors"
        )

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_delete_sponsor_sponsor_line_relation_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor = await sponsor_service.create(SponsorFactory.build())

        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        ssl_service = SponsorSponsorLineServiceDB(test_db)
        relation_data = SponsorSponsorLineSchemaCreate(
            sponsor_id=sponsor.id, sponsor_line_id=sponsor_line.id
        )
        await ssl_service.create(relation_data)

        response = await client.delete(
            f"/api/sponsor_in_sponsor_line/{sponsor.id}in{sponsor_line.id}"
        )

        assert response.status_code == 200
