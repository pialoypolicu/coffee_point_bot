from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseSchema(PydanticBaseModel):
    """Базовая схема с общей конфигурацией."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

class IDSchema(BaseSchema):
    """Базовая схема ID."""

    id: int
