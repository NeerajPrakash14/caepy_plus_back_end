"""Ensure doctors.email and doctors.phone are unique

Revision ID: 003_unique_email_and_phone
Revises: 002_comprehensive_doctor_schema
Create Date: 2026-01-12

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_unique_email_and_phone"
down_revision: Union[str, None] = "002_comprehensive_doctor_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _sqlite_has_index(conn, index_name: str) -> bool:
    rows = conn.exec_driver_sql("PRAGMA index_list('doctors')").fetchall()
    return any(r[1] == index_name for r in rows)

def _postgres_has_index(conn, index_name: str) -> bool:
    row = conn.exec_driver_sql(
        "SELECT 1 FROM pg_indexes WHERE tablename = 'doctors' AND indexname = %s",
        (index_name,),
    ).fetchone()
    return row is not None

def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    email_index = "ux_doctors_email"
    phone_index = "ux_doctors_phone"

    if dialect == "sqlite":
        if not _sqlite_has_index(conn, email_index):
            op.execute(f"CREATE UNIQUE INDEX {email_index} ON doctors (email)")
        if not _sqlite_has_index(conn, phone_index):
            op.execute(f"CREATE UNIQUE INDEX {phone_index} ON doctors (phone)")
        return

    if dialect == "postgresql":
        if not _postgres_has_index(conn, email_index):
            op.execute(f"CREATE UNIQUE INDEX {email_index} ON doctors (email)")
        if not _postgres_has_index(conn, phone_index):
            op.execute(f"CREATE UNIQUE INDEX {phone_index} ON doctors (phone)")
        return

    # Other dialects: best-effort (may fail depending on DB)
    op.execute(f"CREATE UNIQUE INDEX {email_index} ON doctors (email)")
    op.execute(f"CREATE UNIQUE INDEX {phone_index} ON doctors (phone)")

def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    email_index = "ux_doctors_email"
    phone_index = "ux_doctors_phone"

    if dialect == "sqlite":
        op.execute(f"DROP INDEX IF EXISTS {email_index}")
        op.execute(f"DROP INDEX IF EXISTS {phone_index}")
        return

    if dialect == "postgresql":
        op.execute(f"DROP INDEX IF EXISTS {email_index}")
        op.execute(f"DROP INDEX IF EXISTS {phone_index}")
        return

    op.execute(f"DROP INDEX {email_index}")
    op.execute(f"DROP INDEX {phone_index}")
