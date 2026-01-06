from types import NoneType
from typing import Annotated, Union, get_args, get_origin

from pydantic import BaseModel, Field, create_model


class PaginationMetadata(BaseModel):
    page: int
    items_per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


def has_none_in_annotation(annotation) -> bool:
    """Check if None is already in the annotation type."""
    origin = get_origin(annotation)
    if origin is Union or origin is type(str | int | None):
        args = get_args(annotation)
        return NoneType in args
    return annotation is NoneType


def make_fields_optional(model_cls: type[BaseModel]) -> type[BaseModel]:
    """Create a new model with all fields optional from an existing model.

    Args:
        model_cls: The Pydantic BaseModel class to make fields optional.

    Returns:
        A new Pydantic BaseModel class with all fields optional.
    """
    new_fields = {}

    for f_name, f_info in model_cls.model_fields.items():
        field_kwargs = {
            "description": f_info.description,
            "examples": f_info.examples,
            "title": f_info.title,
            "repr": f_info.repr,
            "exclude": f_info.exclude,
            "alias": f_info.alias,
        }

        field_kwargs = {k: v for k, v in field_kwargs.items() if v is not None}

        default_value = Field(None, **field_kwargs)

        if has_none_in_annotation(f_info.annotation):
            new_annotation = f_info.annotation
        else:
            new_annotation = Union[f_info.annotation, None]

        if f_info.metadata:
            new_annotation = Annotated[new_annotation, *f_info.metadata]

        new_fields[f_name] = (new_annotation, default_value)

    return create_model(
        f"{model_cls.__name__}Optional",
        __base__=model_cls,
        **new_fields,
    )
