"""
Pydantic models used in application.

Contains some business logic in form of validators.
"""
__all__ = [
    "Citizen",
    "CitizenPatch",
    "CitizenPresents",
    "Import",
    "PresentsByMonth",
    "TownPercentiles",
    "ImportId",
    "SavedImport",
    "Percentiles",
    "Presents",
]
from datetime import date
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, PositiveInt, confloat, constr, create_model, root_validator, validator


class Gender(str, Enum):
    """Gender enum."""

    male = "male"
    female = "female"


class BaseCitizen(BaseModel):
    """Base class."""

    @validator("birth_date", check_fields=False)
    def date_legit(cls, v: date) -> date:
        """Validate that date of birth is not future."""
        if v > date.today():
            raise ValueError("birth date can't be future")
        return v

    @validator("relatives", check_fields=False)
    def relatives_unique(cls, v: List[int]) -> List[int]:
        """Validate that relatives id's are unique for every citizen."""
        if len(v) > len(set(v)):
            raise ValueError("relatives must be unique")
        return v


class Citizen(BaseCitizen):
    """Citizen model."""

    citizen_id: int = Field(...)
    town: constr(min_length=1, max_length=256) = Field(...)
    street: constr(min_length=1, max_length=256) = Field(...)
    building: constr(min_length=1, max_length=256) = Field(...)
    apartment: PositiveInt = Field(...)
    name: constr(min_length=1, max_length=256) = Field(...)
    birth_date: date = Field(...)
    gender: Gender = Field(...)
    relatives: Optional[List[int]] = None

    class Config:
        """Model config."""

        orm_mode = True
        use_enum_values = True


class CitizenPatch(BaseCitizen):
    """Model used to patch a citizen."""

    town: Optional[constr(min_length=1, max_length=256)]
    street: Optional[constr(min_length=1, max_length=256)]
    building: Optional[constr(min_length=1, max_length=256)]
    apartment: Optional[PositiveInt]
    name: Optional[constr(min_length=1, max_length=256)]
    birth_date: Optional[date]
    gender: Optional[Gender]
    relatives: Optional[List[int]] = None

    class Config:
        """Model config."""

        orm_mode = True
        use_enum_values = True

    @root_validator(pre=True)
    def assert_any(cls, values: Any) -> Any:
        """Validate that at least one of fields is not empty."""
        if all(v is None for v in values.values()):
            raise ValueError("at least one of fields must have value")
        return values


class Import(BaseModel):
    """Import model."""

    data: List[Citizen]

    class Config:
        """Model config."""

        orm_mode = True
        use_enum_values = True

    @validator("data")
    def citizens_ids_unique(cls, v: List[Citizen]) -> List[Citizen]:
        """Validate that every citizen in import has unique id."""
        citizen_ids_set = set()
        citizen_ids = []
        for citizen in v:
            citizen_ids.append(citizen.citizen_id)
            citizen_ids_set.add(citizen.citizen_id)
        if len(citizen_ids) > len(citizen_ids_set):
            raise ValueError("citizen ids in import are not unique")
        return v

    @validator("data")
    def citizens_relatives_mutual(cls, v: List[Citizen]) -> List[Citizen]:
        """Validate that every relation is mutual."""
        relatives = {citizen.citizen_id: set(citizen.relatives) for citizen in v}
        for citizen_id, relative_ids in relatives.items():
            for relative_id in relative_ids:
                if citizen_id not in relatives.get(relative_id, set()):
                    raise ValueError(f"citizen {citizen_id} does not have relation with {relative_id}")
        return v


class CitizenPresents(BaseModel):
    """Number of presents that citizen will buy."""

    citizen_id: int
    presents: int


dynamic_model_args = {str(i): (List[CitizenPresents], Field(...)) for i in range(1, 13)}
PresentsByMonth = create_model("PresentsByMonth", **dynamic_model_args)


class TownPercentiles(BaseModel):
    """Age percentiles for town."""

    town: str = Field(...)
    p50: confloat(ge=0) = Field(...)
    p75: confloat(ge=0) = Field(...)
    p99: confloat(ge=0) = Field(...)


class ImportId(BaseModel):
    """Import id."""

    import_id: PositiveInt


class SavedImport(BaseModel):
    """Saved import."""

    data: ImportId


class Presents(BaseModel):
    """Presents by month."""

    data: PresentsByMonth


class Percentiles(BaseModel):
    """Age percentiles."""

    data: List[TownPercentiles]
