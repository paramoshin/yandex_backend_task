"""Database models."""
from sqlalchemy import Column, Date, ForeignKey, ForeignKeyConstraint, Integer, String, Table
from sqlalchemy.dialects.postgresql import ENUM

from .base import metadata

citizens = Table(
    "citizens",
    metadata,
    Column("import_id", Integer, ForeignKey("imports.import_id"), primary_key=True),
    Column("citizen_id", Integer, primary_key=True, autoincrement=True),
    Column("town", String(256), nullable=False),
    Column("street", String(256), nullable=False),
    Column("building", String(256), nullable=False),
    Column("apartment", Integer, nullable=False),
    Column("name", String(256), nullable=False),
    Column("birth_date", Date, nullable=False),
    Column("gender", ENUM("male", "female", name="gender", create_type=False), nullable=False),
)


imports = Table("imports", metadata, Column("import_id", Integer, primary_key=True, autoincrement=True),)


relations = Table(
    "relations",
    metadata,
    Column("import_id", Integer, primary_key=True),
    Column("citizen", Integer, primary_key=True),
    Column("relative", Integer, primary_key=True),
    ForeignKeyConstraint(("import_id", "citizen"), ("citizens.import_id", "citizens.citizen_id")),
    ForeignKeyConstraint(("import_id", "relative"), ("citizens.import_id", "citizens.citizen_id")),
)
