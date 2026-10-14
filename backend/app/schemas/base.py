"""Shared response-schema base.

All timestamps are stored as naive UTC. Serialized without an offset,
browsers parse them as local time (e.g. East Africa Time) — which skews
payments and audit displays by the timezone offset. This base stamps an
explicit UTC marker on every datetime on the way out.
"""
from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer


class ApiSchema(BaseModel):
    @field_serializer("*", when_used="json")
    def _serialize_datetimes_as_utc(self, value):
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat().replace("+00:00", "Z")
        return value
