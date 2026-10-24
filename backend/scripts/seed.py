"""isi database dari csv hasil generator data sintetis (ml/data/raw).

pemakaian, dari folder backend:
    python scripts/seed.py
    python scripts/seed.py --data ../ml/data/raw

seluruh proses jalan dalam satu transaksi: truncate semua tabel, insert ulang, lalu sinkronkan
sequence id. kalau ada yang gagal, database kembali ke kondisi sebelumnya.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Table, Text, func, insert, select, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import get_engine  # noqa: E402
from app.models import Base  # noqa: E402

DEFAULT_DATA_DIR = BACKEND_DIR.parent / "ml" / "data" / "raw"

# urutan insert mengikuti foreign key, tabel induk lebih dulu
SEED_TABLES = ("users", "materials", "vendors", "vendor_offers", "procurement_requests", "transactions")
# recommendations tidak diisi, tapi ikut dikosongkan karena bergantung pada procurement_requests
TRUNCATE_TABLES = (*SEED_TABLES, "recommendations")
BATCH_SIZE = 1000


def convert(value: str, column) -> object:
    if value == "":
        return None
    kind = column.type
    if isinstance(kind, Boolean):
        if value not in ("true", "false"):
            raise ValueError(f"{column.table.name}.{column.name}: nilai boolean tidak valid {value!r}")
        return value == "true"
    if isinstance(kind, Integer):
        return int(value)
    if isinstance(kind, Numeric):
        return Decimal(value)
    if isinstance(kind, DateTime):
        return datetime.fromisoformat(value)
    if isinstance(kind, Date):
        return date.fromisoformat(value)
    if isinstance(kind, (String, Text)):
        return value
    raise TypeError(f"{column.table.name}.{column.name}: tipe {kind!r} belum didukung")


def read_table(data_dir: Path, table: Table) -> list[dict]:
    path = data_dir / f"{table.name}.csv"
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        expected = [c.name for c in table.columns]
        if reader.fieldnames != expected:
            raise ValueError(f"{path.name}: kolom {reader.fieldnames} tidak sama dengan tabel {expected}")
        return [{name: convert(row[name], table.c[name]) for name in expected} for row in reader]


async def seed(data_dir: Path) -> dict[str, tuple[int, int, int]]:
    engine = get_engine()
    if engine is None:
        raise RuntimeError("DATABASE_URL belum di-set di backend/.env")

    # hanya 6 file tabel yang dibaca, file berawalan "_" tidak pernah disentuh
    tables = {name: Base.metadata.tables[name] for name in SEED_TABLES}
    rows = {name: read_table(data_dir, table) for name, table in tables.items()}

    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(TRUNCATE_TABLES)} RESTART IDENTITY CASCADE"))
        for name, table in tables.items():
            for start in range(0, len(rows[name]), BATCH_SIZE):
                await conn.execute(insert(table), rows[name][start : start + BATCH_SIZE])

        # sequence id dimajukan ke max(id) + 1 supaya insert baru dari api tidak bentrok
        for name in TRUNCATE_TABLES:
            await conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence(:name, 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {name}), 0) + 1, false)"
            ), {"name": name})

    # cek ulang setelah commit dengan koneksi baru
    result = {}
    async with engine.connect() as conn:
        for name in TRUNCATE_TABLES:
            table = Base.metadata.tables[name]
            count = (await conn.execute(select(func.count()).select_from(table))).scalar_one()
            sequence = (await conn.execute(
                text("SELECT pg_get_serial_sequence(:name, 'id')"), {"name": name}
            )).scalar_one()
            last_value, is_called = (await conn.execute(text(f"SELECT last_value, is_called FROM {sequence}"))).one()
            next_id = last_value + 1 if is_called else last_value
            result[name] = (len(rows.get(name, [])), count, next_id)
    await engine.dispose()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="seed database dari csv generator data sintetis")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR, help="folder csv (default ml/data/raw)")
    args = parser.parse_args()
    data_dir = args.data.resolve()

    manifest = json.loads((data_dir / "_manifest.json").read_text(encoding="utf-8"))
    print(f"seed database dari {data_dir} (seed generator {manifest['seed']}, config {manifest['config_hash']})")

    result = asyncio.run(seed(data_dir))

    print(f"\n{'tabel':<22} {'csv':>7} {'db':>7} {'id berikutnya':>14}  cek")
    ok = True
    for name, (csv_count, db_count, next_id) in result.items():
        match = csv_count == db_count
        ok &= match
        print(f"{name:<22} {csv_count:>7,} {db_count:>7,} {next_id:>14,}  {'sama' if match else 'BEDA'}")
    print("\nsemua jumlah baris sama dengan csv" if ok else "\nADA JUMLAH BARIS YANG BEDA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
