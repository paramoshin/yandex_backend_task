from datetime import date, timedelta

import pytest
from utils import generate_citizen


def age2date(years: int, days: int = 0) -> str:
    """
    Возвращает дату рождения для жителя, возраст которого составляет years лет
    и days дней. Позволяет представлять дату рождения жителя в виде возраста человека в днях
    и годах, что гораздо нагляднее в тестах.
    """
    _today = date.today()
    birth_date = _today.replace(year=_today.year - years)
    birth_date -= timedelta(days=days)
    return birth_date.strftime("%Y-%m-%d")


def test_full_years(migrated_postgres, client):
    dataset = [
        generate_citizen(birth_date=age2date(years=10, days=364), town="Москва", citizen_id=1),
        generate_citizen(birth_date=age2date(years=30, days=364), town="Москва", citizen_id=2),
        generate_citizen(birth_date=age2date(years=50, days=364), town="Москва", citizen_id=3),
    ]
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/towns/stat/percentile/age"

    expected = [{"town": "Москва", "p50": 30.0, "p75": 40.0, "p99": 49.6}]

    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected


def test_birthday_today(migrated_postgres, client):
    dataset = [generate_citizen(birth_date=age2date(years=10), town="Москва")]
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/towns/stat/percentile/age"

    expected = [{"town": "Москва", "p50": 10, "p75": 10, "p99": 10}]

    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected


def test_empty(migrated_postgres, client):
    r = client.post("/imports", json={"data": []})
    print(r.json())
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/towns/stat/percentile/age"
    expected = []
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected
