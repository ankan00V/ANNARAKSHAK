"""Copy the AnnRakshak database from one engine to another — in practice the
local SQLite file to Postgres (Neon).

    ../.venv/bin/python migrate_db.py --to "$NEON_DB_URL_DIRECT"             # dry run: counts only
    ../.venv/bin/python migrate_db.py --to "$NEON_DB_URL_DIRECT" --apply     # copy
    ../.venv/bin/python migrate_db.py --to ... --apply --replace             # empty the target first

Tables are copied parent-first (the ORM's dependency order), ids are kept so
every foreign key still points at the same row, and Postgres sequences are
moved past the copied ids. Use the DIRECT (non-pooled) URL for the copy.
The target must be empty unless --replace is given; nothing is ever merged.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import func, inspect, select, text

from app.config import DB_URL
from app.db import Base, init_db, make_engine

BATCH = 500


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=DB_URL, help="source URL (default: the configured database)")
    ap.add_argument("--to", dest="dst", required=True, help="target URL (use Neon's direct endpoint)")
    ap.add_argument("--apply", action="store_true", help="actually copy (default is a dry run)")
    ap.add_argument("--replace", action="store_true", help="delete everything in the target first")
    args = ap.parse_args()

    src, dst = make_engine(args.src), make_engine(args.dst)
    if src.url == dst.url:
        sys.exit("source and target are the same database")
    init_db(src)  # bring an older source up to the current schema first
    tables = Base.metadata.sorted_tables
    with src.connect() as s:
        counts = {t.name: s.scalar(select(func.count()).select_from(t)) for t in tables}
    print(f"source {src.url.render_as_string(hide_password=True)}")
    for name, n in counts.items():
        print(f"  {name:20s} {n:6d}")
    if not args.apply:
        print("dry run — add --apply to copy")
        return

    init_db(dst)  # create the schema on the target
    with dst.begin() as d:
        existing = {t.name: d.scalar(select(func.count()).select_from(t)) for t in tables}
        if any(existing.values()):
            if not args.replace:
                sys.exit(f"target is not empty ({ {k: v for k, v in existing.items() if v} }); use --replace")
            for t in reversed(tables):
                d.execute(t.delete())

    with src.connect() as s, dst.begin() as d:
        for t in tables:
            rows = [dict(r._mapping) for r in s.execute(select(t))]
            for i in range(0, len(rows), BATCH):
                d.execute(t.insert(), rows[i:i + BATCH])
            print(f"  copied {t.name:20s} {len(rows):6d}")
        if dst.dialect.name == "postgresql":
            for t in tables:
                pk = [c for c in t.primary_key.columns]
                if len(pk) == 1 and pk[0].autoincrement is not False and pk[0].type.python_type is int:
                    d.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('\"{t.name}\"', '{pk[0].name}'), "
                        f"COALESCE((SELECT MAX({pk[0].name}) FROM \"{t.name}\"), 0) + 1, false)"))

    with dst.connect() as d:
        bad = {t.name: (counts[t.name], d.scalar(select(func.count()).select_from(t)))
               for t in tables if d.scalar(select(func.count()).select_from(t)) != counts[t.name]}
    if bad:
        sys.exit(f"row counts differ after copy: {bad}")
    print(f"done — {sum(counts.values())} rows in {len(tables)} tables; target tables: "
          f"{len(inspect(dst).get_table_names())}")


if __name__ == "__main__":
    main()
