from sqlmodel import SQLModel, Field, Column
from sqlalchemy import BigInteger
from datetime import datetime


class ShortURL(SQLModel, table=True):
    snowflake_id: int = Field(
        sa_column=Column(BigInteger(), primary_key=True),
        description="Snowflake-style ID (primary key)"
    )
    original_url: str
    short_code: str = Field(index=True, unique=True, description="Base62 encoded short code")
    created_at: datetime = Field(default_factory=datetime.utcnow)
