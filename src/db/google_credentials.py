from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    select,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import Base


class GoogleCredentials(Base):
    __tablename__ = "google_credentials"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_type = Column(String, nullable=False)
    scope = Column(String, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


async def save_google_credentials(
    session: AsyncSession,
    user_id: int,
    access_token: str,
    refresh_token: Optional[str],
    token_type: str,
    scope: str,
    expires_in: Optional[int],
) -> GoogleCredentials:
    result = await session.execute(
        select(GoogleCredentials).where(GoogleCredentials.user_id == user_id)
    )
    creds = result.scalar_one_or_none()

    expires_in = expires_in or 3600
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    if creds:
        creds.access_token = access_token
        creds.refresh_token = refresh_token
        creds.token_type = token_type
        creds.scope = scope
        creds.expires_at = expires_at
    else:
        creds = GoogleCredentials(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            scope=scope,
            expires_at=expires_at,
        )
        session.add(creds)

    return creds
