from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATA_DIR, DB_URL


class Base(DeclarativeBase):
    pass


def make_engine(url: str = DB_URL):
    if url.startswith("sqlite:///"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        # SQLite ignores FOREIGN KEY and CHECK-backed invariants unless asked.
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the first release. create_all() does not alter existing
# tables, so add any that an older database lacks (SQLite ADD COLUMN is cheap).
ADDED_COLUMNS = {
    "farm": {"soil_ph": "FLOAT", "soil_ph_on": "DATE"},
    "sensor_reading": {"soil_ph": "FLOAT", "soil_moisture_pct": "FLOAT"},
}


def init_db(bind=None) -> None:
    from sqlalchemy import inspect, text  # noqa: PLC0415

    from app import models  # noqa: F401  registers the tables

    eng = bind or engine
    Base.metadata.create_all(bind=eng)
    insp = inspect(eng)
    with eng.begin() as conn:
        for table, cols in ADDED_COLUMNS.items():
            have = {c["name"] for c in insp.get_columns(table)}
            for col, typ in cols.items():
                if col not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typ}"))
