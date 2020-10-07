"""Database models."""
from sqlalchemy import Column, Date, Enum, ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.dialects.postgresql import ENUM

from .base import Base


class Citizen(Base):
    """Citizen model."""

    __tablename__ = "citizens"

    import_id = Column("import_id", Integer, ForeignKey("imports.import_id"), primary_key=True)
    citizen_id = Column("citizen_id", Integer, primary_key=True, autoincrement=True)
    town = Column("town", String(256), nullable=False)
    street = Column("street", String(256), nullable=False)
    building = Column("building", String(256), nullable=False)
    apartment = Column("apartment", Integer, nullable=False)
    name = Column("name", String(256), nullable=False)
    birth_date = Column("birth_date", Date, nullable=False)
    gender = Column("gender", ENUM("male", "female", name="gender", create_type=False), nullable=False)


class Import(Base):
    """Import model."""

    __tablename__ = "imports"

    import_id = Column("import_id", Integer, primary_key=True, autoincrement=True)


class Relation(Base):
    """Relation model."""

    __tablename__ = "relations"

    import_id = Column("import_id", Integer, primary_key=True)
    citizen = Column("citizen", Integer, primary_key=True)
    relative = Column("relative", Integer, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(("import_id", "citizen"), ("citizens.import_id", "citizens.citizen_id")),
        ForeignKeyConstraint(("import_id", "relative"), ("citizens.import_id", "citizens.citizen_id")),
    )
