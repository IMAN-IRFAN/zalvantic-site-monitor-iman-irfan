from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (Index("ix_results_site_time", "site", "checked_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column(String(255))
    check_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


def get_session_factory(db_url: str = "sqlite:///monitor.db"):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(engine)


def save_result(session_factory, site: str, check_type: str, status: str, value: float | None):
    with session_factory() as session:
        session.add(Result(site=site, check_type=check_type, status=status, value=value))
        session.commit()