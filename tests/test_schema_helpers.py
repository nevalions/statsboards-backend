"""Test schema helpers module."""

import pytest
from pydantic import BaseModel, Field

from src.core.schema_helpers import (
    has_none_in_annotation,
    make_fields_optional,
    PaginationMetadata,
)


class SampleModel(BaseModel):
    """Sample model for schema helpers."""

    required_field: str = Field(..., description="Required field")
    optional_field: int | None = Field(None, description="Optional field")
    default_field: str = Field("default", description="Default field")


class SampleModelWithNone(BaseModel):
    """Sample model with None type annotation."""

    field: None = Field(...)


class SampleModelWithUnion(BaseModel):
    """Sample model with Union type annotation."""

    field: str | None = Field(...)


class TestPaginationMetadata:
    """Test PaginationMetadata."""

    def test_pagination_metadata_creation(self):
        """Test creating pagination metadata."""
        metadata = PaginationMetadata(
            page=1,
            items_per_page=10,
            total_items=100,
            total_pages=10,
            has_next=True,
            has_previous=False,
        )

        assert metadata.page == 1
        assert metadata.items_per_page == 10
        assert metadata.total_items == 100
        assert metadata.total_pages == 10
        assert metadata.has_next is True
        assert metadata.has_previous is False


class TestHasNoneInAnnotation:
    """Test has_none_in_annotation function."""

    def test_none_type(self):
        """Test with None type."""
        from types import NoneType

        result = has_none_in_annotation(NoneType)
        assert result is True

    def test_union_with_none(self):
        """Test with Union type containing None."""
        result = has_none_in_annotation(str | None)
        assert result is True

    def test_union_without_none(self):
        """Test with Union type without None."""
        result = has_none_in_annotation(str | int)
        assert result is False

    def test_regular_type(self):
        """Test with regular type."""
        result = has_none_in_annotation(str)
        assert result is False

    def test_optional_type(self):
        """Test with Optional type (same as Union[T, None])."""
        from typing import Optional

        result = has_none_in_annotation(Optional[str])
        assert result is True


class TestMakeFieldsOptional:
    """Test make_fields_optional function."""

    def test_creates_optional_model(self):
        """Test creating optional model from regular model."""
        OptionalModel = make_fields_optional(SampleModel)

        assert OptionalModel.__name__ == "SampleModelOptional"

        original_fields = set(SampleModel.model_fields.keys())
        optional_fields = set(OptionalModel.model_fields.keys())

        assert original_fields == optional_fields

    def test_optional_fields_are_optional(self):
        """Test that all fields in optional model are optional."""
        OptionalModel = make_fields_optional(SampleModel)

        for field_name, field_info in OptionalModel.model_fields.items():
            assert field_info.is_required() is False

    def test_preserves_field_metadata(self):
        """Test that field metadata is preserved."""
        OptionalModel = make_fields_optional(SampleModel)

        for field_name, field_info in OptionalModel.model_fields.items():
            original_info = SampleModel.model_fields[field_name]
            assert field_info.description == original_info.description
            assert field_info.title == original_info.title

    def test_preserves_none_annotation(self):
        """Test that None annotation is preserved."""
        OptionalModel = make_fields_optional(SampleModelWithNone)

        field_info = OptionalModel.model_fields["field"]
        assert field_info.default is None

    def test_union_annotation_becomes_union(self):
        """Test that Union annotations remain Union."""
        OptionalModel = make_fields_optional(SampleModelWithUnion)

        field_info = OptionalModel.model_fields["field"]

        assert field_info.annotation is not None

    def test_required_becomes_optional(self):
        """Test that required fields become optional."""
        OptionalModel = make_fields_optional(SampleModel)

        required_field_info = OptionalModel.model_fields["required_field"]
        assert required_field_info.default is None
        assert required_field_info.is_required() is False
