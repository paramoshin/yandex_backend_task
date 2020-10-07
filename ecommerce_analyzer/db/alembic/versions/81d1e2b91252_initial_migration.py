"""initial migration

Revision ID: 81d1e2b91252
Revises:
Create Date: 2020-10-06 17:15:02.402053

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "81d1e2b91252"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "imports",
        sa.Column("import_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("import_id", name=op.f("pk__imports")),
    )
    op.create_table(
        "citizens",
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("citizen_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("town", sa.String(length=256), nullable=False),
        sa.Column("street", sa.String(length=256), nullable=False),
        sa.Column("building", sa.String(length=256), nullable=False),
        sa.Column("apartment", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("gender", postgresql.ENUM("male", "female", name="gender"), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.import_id"], name=op.f("fk__citizens__import_id__imports")),
        sa.PrimaryKeyConstraint("import_id", "citizen_id", name=op.f("pk__citizens")),
    )
    op.create_table(
        "relations",
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("citizen", sa.Integer(), nullable=False),
        sa.Column("relative", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_id", "citizen"],
            ["citizens.import_id", "citizens.citizen_id"],
            name=op.f("fk__relations__import_id_citizen__citizens"),
        ),
        sa.ForeignKeyConstraint(
            ["import_id", "relative"],
            ["citizens.import_id", "citizens.citizen_id"],
            name=op.f("fk__relations__import_id_relative__citizens"),
        ),
        sa.PrimaryKeyConstraint("import_id", "citizen", "relative", name=op.f("pk__relations")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("relations")
    op.drop_table("citizens")
    op.drop_table("imports")
    op.execute("DROP TYPE gender;")
    # ### end Alembic commands ###
