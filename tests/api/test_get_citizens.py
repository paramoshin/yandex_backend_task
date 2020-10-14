import pytest
from utils import LONGEST_STR, MAX_INT, compare_citizen_groups, generate_citizen, generate_citizens

dataset = [
    generate_citizen(citizen_id=1, relatives=[2, 3]),
    generate_citizen(citizen_id=2, relatives=[1]),
    generate_citizen(citizen_id=3, relatives=[1]),
    generate_citizen(citizen_id=4, relatives=[]),
    generate_citizen(citizen_id=5, name="Джейн", gender="male", birth_date="2020-02-17", relatives=[5]),
]


def test_get_citizens(migrated_postgres, client):
    r = client.post("/imports", json={"data": dataset})
    import_id = r.json()["data"]["import_id"]

    response = client.get(f"/imports/{import_id}/citizens")
    assert response.status_code == 200
    assert compare_citizen_groups(response.json()["data"], dataset)
