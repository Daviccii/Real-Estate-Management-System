"""Bounded pagination query parameters shared by every list endpoint.

Raw `skip: int = 0, limit: int = 100` parameters are unbounded: a caller can
send `limit=-1` (unlimited in SQLite/SQL semantics) or `limit=10_000_000` and
force the database to materialize an arbitrary amount of rows. These annotated
types clamp both ends at the HTTP layer so the limits hold for every endpoint
that adopts them, matching the existing Query(ge=1, le=settings.MAX_PAGE_SIZE)
usage elsewhere.
"""
from typing import Annotated

from fastapi import Query

from app.config.settings import settings

SkipParam = Annotated[int, Query(ge=0)]
LimitParam = Annotated[int, Query(ge=1, le=settings.MAX_PAGE_SIZE)]
