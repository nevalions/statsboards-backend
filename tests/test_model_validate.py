from src.teams.schemas import TeamSchema, TeamSchemaCreate, TeamSchemaUpdate


class DummyTeamModel:
    """Mock database model to test model_validate."""

    def __init__(
        self,
        id: int,
        title: str,
        city: str = "City",
        description: str = "",
        sport_id: int = 1,
    ):
        self.id = id
        self.title = title
        self.city = city
        self.description = description
        self.team_eesl_id = None
        self.team_logo_url = ""
        self.team_logo_icon_url = ""
        self.team_logo_web_url = ""
        self.team_color = "#c01c28"
        self.sponsor_line_id = None
        self.main_sponsor_id = None
        self.sport_id = sport_id


class TestPydanticModelValidation:
    """Test suite for Pydantic model_validate usage."""

    def test_team_schema_model_validate_from_model(self):
        """Test TeamSchema.model_validate converts database model to schema."""
        db_model = DummyTeamModel(
            id=1,
            title="Test Team",
            city="Test City",
            description="Test Description",
            sport_id=1,
        )

        schema = TeamSchema.model_validate(db_model)

        assert schema.id == 1
        assert schema.title == "Test Team"
        assert schema.city == "Test City"
        assert schema.description == "Test Description"
        assert schema.sport_id == 1

    def test_team_schema_model_validate_creates_valid_dict(self):
        """Test that model_validate creates valid Pydantic model."""
        db_model = DummyTeamModel(
            id=2,
            title="Team 2",
            sport_id=1,
        )

        schema = TeamSchema.model_validate(db_model)
        schema_dict = schema.model_dump()

        assert isinstance(schema_dict, dict)
        assert schema_dict["id"] == 2
        assert schema_dict["title"] == "Team 2"
        assert "id" in schema_dict
        assert "title" in schema_dict
        assert "city" in schema_dict

    def test_team_schema_create_validation(self):
        """Test TeamSchemaCreate validates input."""
        data = {
            "title": "Valid Team",
            "city": "Valid City",
            "description": "Valid Description",
            "sport_id": 1,
        }

        schema = TeamSchemaCreate(**data)

        assert schema.title == "Valid Team"
        assert schema.city == "Valid City"
        assert schema.description == "Valid Description"
        assert schema.sport_id == 1

    def test_team_schema_update_validation(self):
        """Test TeamSchemaUpdate validates optional fields."""
        data = {"title": "Updated Team"}

        schema = TeamSchemaUpdate(**data)

        assert schema.title == "Updated Team"
        assert schema.city is None
        assert schema.description is None

    def test_multiple_model_validate_calls(self):
        """Test that model_validate can be called multiple times safely."""
        db_model = DummyTeamModel(
            id=3,
            title="Team 3",
            sport_id=1,
        )

        schema1 = TeamSchema.model_validate(db_model)
        schema2 = TeamSchema.model_validate(db_model)

        assert schema1.id == schema2.id
        assert schema1.title == schema2.title
        assert schema1.model_dump() == schema2.model_dump()

    def test_model_validate_preserves_types(self):
        """Test that model_validate preserves data types."""
        db_model = DummyTeamModel(
            id=4,
            title="Team 4",
            sport_id=42,
        )

        schema = TeamSchema.model_validate(db_model)

        assert isinstance(schema.id, int)
        assert isinstance(schema.title, str)
        assert isinstance(schema.sport_id, int)
        assert isinstance(schema.city, str)

    def test_model_validate_with_none_values(self):
        """Test model_validate handles None values correctly."""
        db_model = DummyTeamModel(
            id=5,
            title="Team 5",
            sport_id=1,
        )
        db_model.team_eesl_id = None
        db_model.sponsor_line_id = None
        db_model.main_sponsor_id = None

        schema = TeamSchema.model_validate(db_model)

        assert schema.team_eesl_id is None
        assert schema.sponsor_line_id is None
        assert schema.main_sponsor_id is None
        assert schema.id == 5
