import json
from datetime import date, timedelta

import pytest
from utils import LONGEST_STR, MAX_INT, compare_citizen_groups, generate_citizen, generate_citizens


def test_successful_patch(migrated_postgres, client):
    dataset = [
        generate_citizen(
            citizen_id=1,
            name="Иванов Иван Иванович",
            gender="male",
            birth_date="2020-01-01",
            town="Некий город",
            street="Некая улица",
            building="Некое строение",
            apartment=1,
            relatives=[2],
        ),
        generate_citizen(citizen_id=2, relatives=[1]),
        generate_citizen(citizen_id=3, relatives=[]),
    ]
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/citizens/1"

    dataset[0]["name"] = "Сидорова Василиса Петровна"
    patch = {"name": dataset[0]["name"]}
    response = client.patch(url, data=json.dumps(patch))
    assert response.status_code == 200
    assert response.json() == dataset[0]

    dataset[0]["gender"] = "female"
    dataset[0]["birth_date"] = "2020-01-02"
    dataset[0]["town"] = "Другой город"
    dataset[0]["street"] = "Другая улица"
    dataset[0]["building"] = "Другое строение"
    dataset[0]["apartment"] = 2
    dataset[0]["relatives"] = [3]
    patch = dataset[0].copy()
    patch.pop("citizen_id")
    response = client.patch(url, data=json.dumps(patch))
    assert response.status_code == 200
    assert response.json() == dataset[0]


def test_wrong_patch(migrated_postgres, client):
    citizen = generate_citizen(citizen_id=1)
    r = client.post("/imports", json={"data": [citizen]})
    import_id = r.json()["data"]["import_id"]
    url = f"/imports/{import_id}/citizens/1"
    patch = {"birth_date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")}
    citizen.update(patch)
    response = client.patch(url, data=json.dumps(patch))
    assert response.status_code == 400
