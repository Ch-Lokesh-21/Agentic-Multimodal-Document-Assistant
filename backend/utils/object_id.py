from typing import Annotated, Any
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2 with JSON serialization."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Define Pydantic validation and serialization schema."""
        def serialize_objectid(value: Any, info):
            """Serialize as str for JSON, ObjectId for Python/MongoDB."""
            if info.mode == 'json':
                return str(value)
            return value

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_objectid,
                info_arg=True,
                return_schema=core_schema.str_schema(),
                when_used='json-unless-none',
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Define JSON schema representation."""
        return {
            "type": "string",
            "description": "MongoDB ObjectId as 24-character hex string",
            "example": "507f1f77bcf86cd799439011",
        }

    @classmethod
    def validate(cls, value: Any) -> "PyObjectId":
        """Validate and convert value to PyObjectId."""
        if isinstance(value, cls):
            return value
        if isinstance(value, ObjectId):
            return cls(str(value))
        if isinstance(value, str):
            if not ObjectId.is_valid(value):
                raise ValueError(f"Invalid ObjectId string: {value}")
            return cls(value)
        raise ValueError(f"Cannot convert {type(value).__name__} to ObjectId")

    @classmethod
    def from_str(cls, value: str) -> "PyObjectId":
        """Create PyObjectId from string."""
        return cls.validate(value)

    def __str__(self) -> str:
        """Return string representation."""
        return super().__str__()

    def __repr__(self) -> str:
        """Return repr string."""
        return f"PyObjectId('{super().__str__()}')"

    def __hash__(self) -> int:
        """Make hashable for use in sets/dict keys."""
        return hash(str(self))


def create_object_id() -> PyObjectId:
    """
    Factory function to create a new PyObjectId.

    Use with Field(default_factory=create_object_id)

    Returns:
        New PyObjectId instance
    """
    return PyObjectId()


def validate_object_id(value: str) -> bool:
    """
    Check if a string is a valid ObjectId.

    Args:
        value: String to validate

    Returns:
        True if valid, False otherwise
    """
    return ObjectId.is_valid(value)


ObjectIdStr = Annotated[str, "MongoDB ObjectId as string"]
