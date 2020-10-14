from typing import Any, Mapping

import pytest
from utils import generate_citizen


def make_response(values: Mapping[str, Any] = None):
    """
    Генерирует словарь, в котором ключи месяцы, а значения по умолчанию - [].
    Позволяет записать ожидаемый ответ в краткой форме.
    """
    return {str(month): values.get(str(month), []) if values else [] for month in range(1, 13)}


def test_multiple_relaties(migrated_postgres, client):
    dataset = [
        generate_citizen(citizen_id=1, birth_date="2019-12-31", relatives=[2, 3]),
        generate_citizen(citizen_id=2, birth_date="2020-02-11", relatives=[1]),
        generate_citizen(citizen_id=3, birth_date="2020-02-17", relatives=[1]),
    ]
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/citizens/birthdays"

    expected = make_response(
        {
            "2": [{"citizen_id": 1, "presents": 2}],
            "12": [{"citizen_id": 2, "presents": 1}, {"citizen_id": 3, "presents": 1}],
        }
    )
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected


def test_self_relative(migrated_postgres, client):
    dataset = [generate_citizen(citizen_id=1, name="Джейн", gender="male", birth_date="2020-02-17", relatives=[1])]
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/citizens/birthdays"

    expected = make_response({"2": [{"citizen_id": 1, "presents": 1}]})
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected


def test_no_relatives(migrated_postgres, client):
    dataset = [
        generate_citizen(citizen_id=1, birth_date="2019-12-31", relatives=[]),
        generate_citizen(citizen_id=2, birth_date="2020-02-11", relatives=[]),
        generate_citizen(citizen_id=3, birth_date="2020-02-17", relatives=[]),
    ]
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/citizens/birthdays"

    expected = make_response()
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected


def test_empty(migrated_postgres, client):
    r = client.post("/imports", json={"data": []})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/citizens/birthdays"

    expected = make_response()
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["data"] == expected
