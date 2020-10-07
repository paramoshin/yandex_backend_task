from datetime import date, timedelta

from utils import LONGEST_STR, MAX_INT, compare_citizen_groups, generate_citizen, generate_citizens


def test_successful_save(migrated_postgres, analyzer, client):
    citizens = generate_citizens(citizens_num=500, relations_num=50,)
    response = client.post("/imports", json={"data": citizens})
    print(response.json())
    assert response.status_code == 201


def test_wrong_dates(migrated_postgres, analyzer, client):
    body = {"data": [generate_citizen(birth_date=(date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))]}
    response = client.post("/imports", json=body)
    assert response.status_code == 400


def test_non_unique_ids(migrated_postgres, analyzer, client):
    body = {"data": [generate_citizen(citizen_id=1), generate_citizen(citizen_id=1),]}
    response = client.post("/imports", json=body)
    assert response.status_code == 400


def test_non_mutual_relatives(migrated_postgres, analyzer, client):
    body = {"data": [dict(citizen_id=1, relatives=[2]), dict(citizen_id=2, relatives=[]),]}
    response = client.post("/imports", json=body)
    assert response.status_code == 400
