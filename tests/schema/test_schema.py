from datetime import date, timedelta

import pytest
from api.scheme import BaseCitizen, Citizen, CitizenPatch, Import
from pydantic import ValidationError
from utils import generate_citizen


def test_base_citizen():
    assert BaseCitizen.__name__ == "BaseCitizen"
    assert BaseCitizen.__validators__.keys() == {"birth_date", "relatives"}


def test_citizen():
    kwargs = dict(
        citizen_id=1,
        town="Town",
        street="Street",
        building="97",
        apartment=1,
        name="John Doe",
        birth_date=date(year=1990, month=1, day=1),
        gender="male",
        relatives=[],
    )
    citizen = Citizen(**kwargs)
    for k, v in kwargs.items():
        assert v == getattr(citizen, k)

    wrong_date_kwargs = kwargs.copy()
    wrong_date_kwargs["birth_date"] = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        Citizen(**wrong_date_kwargs)

    non_unique_relatives_kwargs = kwargs.copy()
    non_unique_relatives_kwargs["relatives"] = [2, 3, 4, 4, 5]
    with pytest.raises(ValidationError):
        Citizen(**non_unique_relatives_kwargs)


def test_citizen_patch():
    kwargs = dict(name="Jonny", building="97a", relatives=[2])
    citizen_patch = CitizenPatch(**kwargs)
    for k, v in kwargs.items():
        value = getattr(citizen_patch, k)
        if isinstance(value, date):
            value = value.strftime("%Y-%m-%d")
        assert v == value

    with pytest.raises(ValidationError):
        CitizenPatch()


def test_import():
    dataset = [
        generate_citizen(citizen_id=1, relatives=[2, 3]),
        generate_citizen(citizen_id=2, relatives=[1]),
        generate_citizen(citizen_id=3, relatives=[1]),
        generate_citizen(citizen_id=4, relatives=[]),
        generate_citizen(citizen_id=5, name="Джейн", gender="male", birth_date="2020-02-17", relatives=[5]),
    ]
    import_obj = Import(data=dataset)
    for i, citizen in enumerate(dataset):
        for k, v in citizen.items():
            value = getattr(import_obj.data[i], k)
            if isinstance(value, date):
                value = value.strftime("%Y-%m-%d")
            assert v == value

    with pytest.raises(ValidationError):
        dataset = [
            generate_citizen(citizen_id=1),
            generate_citizen(citizen_id=1),
        ]
        Import(data=dataset)

    with pytest.raises(ValidationError):
        dataset = [
            generate_citizen(citizen_id=1, relatives=[2, 3]),
            generate_citizen(citizen_id=2, relatives=[1]),
            generate_citizen(citizen_id=3, relatives=[]),
        ]
        Import(data=dataset)
