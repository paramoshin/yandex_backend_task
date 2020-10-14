import time
from datetime import date
from random import choice, randint, randrange, shuffle
from typing import Any, Dict, Iterable, List, Mapping, Optional

import faker
import psycopg2

fake = faker.Faker("ru_RU")
MAX_INT = 2147483647
LONGEST_STR = "ё" * 256


def generate_citizen(
    citizen_id: Optional[int] = None,
    name: Optional[str] = None,
    birth_date: Optional[str] = None,
    gender: Optional[str] = None,
    town: Optional[str] = None,
    street: Optional[str] = None,
    building: Optional[str] = None,
    apartment: Optional[int] = None,
    relatives: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Создает и возвращает жителя, автоматически генерируя данные для не
    указанных полей.
    """
    if citizen_id is None:
        citizen_id = randint(0, MAX_INT)

    if gender is None:
        gender = choice(("female", "male"))

    if name is None:
        name = fake.name_female() if gender == "female" else fake.name_male()

    if birth_date is None:
        birth_date = fake.date_of_birth(minimum_age=0, maximum_age=95).strftime("%Y-%m-%d")

    if town is None:
        town = fake.city_name()

    if street is None:
        street = fake.street_name()

    if building is None:
        building = str(randrange(1, 100))

    if apartment is None:
        apartment = randrange(1, 120)

    if relatives is None:
        relatives = []

    return {
        "citizen_id": citizen_id,
        "name": name,
        "birth_date": birth_date,
        "gender": gender,
        "town": town,
        "street": street,
        "building": building,
        "apartment": apartment,
        "relatives": relatives,
    }


def generate_citizens(
    citizens_num: int,
    relations_num: Optional[int] = None,
    unique_towns: int = 20,
    start_citizen_id: int = 0,
    **citizen_kwargs,
) -> List[Dict[str, Any]]:
    """
    Генерирует список жителей.
    :param citizens_num: Количество жителей
    :param relations_num: Количество родственных связей (подразумевается одна
            связь между двумя людьми)
    :param unique_towns: Кол-во уникальных городов в выгрузке
    :param start_citizen_id: С какого citizen_id начинать
    :param citizen_kwargs: Аргументы для функции generate_citizen
    """
    # Ограничнный набор городов
    towns = [fake.city_name() for _ in range(unique_towns)]

    # Создаем жителей
    max_citizen_id = start_citizen_id + citizens_num - 1
    citizens = {}
    for citizen_id in range(start_citizen_id, max_citizen_id + 1):
        citizen_kwargs["town"] = citizen_kwargs.get("town", choice(towns))
        citizens[citizen_id] = generate_citizen(citizen_id=citizen_id, **citizen_kwargs)

    # Создаем родственные связи
    unassigned_relatives = relations_num or citizens_num // 10
    shuffled_citizen_ids = list(citizens.keys())
    while unassigned_relatives:
        # Перемешиваем список жителей
        shuffle(shuffled_citizen_ids)

        # Выбираем жителя, кому ищем родственника
        citizen_id = shuffled_citizen_ids[0]

        # Выбираем родственника для этого жителя и проставляем
        # двустороннюю связь
        for relative_id in shuffled_citizen_ids[1:]:
            if relative_id not in citizens[citizen_id]["relatives"]:
                citizens[citizen_id]["relatives"].append(relative_id)
                citizens[relative_id]["relatives"].append(citizen_id)
                break
        else:
            raise ValueError("Unable to choose relative for citizen")
        unassigned_relatives -= 1

    return list(citizens.values())


def normalize_citizen(citizen):
    """
    Преобразует объект с жителем для сравнения с другими.
    """
    normalized = {
        **{k: v for k, v in sorted(citizen.items(), key=lambda item: item[0])},
        "relatives": sorted(citizen["relatives"]),
    }
    if "birth_date" in normalized:
        if type(normalized["birth_date"]) is date:
            normalized["birth_date"] = normalized["birth_date"].strftime("%Y-%m-%d")
    return normalized


def compare_citizens(left: Mapping, right: Mapping) -> bool:
    return normalize_citizen(left) == normalize_citizen(right)


def compare_citizen_groups(left: Iterable, right: Iterable) -> bool:
    left = [normalize_citizen(citizen) for citizen in left]
    left.sort(key=lambda citizen: citizen["citizen_id"])

    right = [normalize_citizen(citizen) for citizen in right]
    right.sort(key=lambda citizen: citizen["citizen_id"])
    return left == right


def wait_for_pg_container(
    user: str, password: str, host: str, port: str, db: str, attempts: int = 10, timeout: float = 0.1
):
    for _ in range(attempts):
        try:
            conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port, connect_timeout=1)
        except Exception:
            time.sleep(timeout)
            timeout *= 2
        else:
            conn.close()
            return
    else:
        raise RuntimeError("Couldn't connect to postgres")
