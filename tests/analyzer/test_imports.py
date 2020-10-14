from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import analyzer
import pytest
from api.scheme import Citizen, Import
from utils import LONGEST_STR, MAX_INT, compare_citizen_groups, generate_citizen, generate_citizens

Case = Tuple[Optional[callable], List[Union[dict, Citizen]]]

CORRECT_CASES: List[Case] = [
    # Житель без родственников.
    # Обработчик должен корректно создавать выгрузку с одним жителем.
    (generate_citizen, [dict(relatives=[])],),
    # Житель с несколькими родственниками.
    # Обработчик должен корректно добавлять жителей и создавать
    # родственные связи.
    (
        generate_citizen,
        [dict(citizen_id=1, relatives=[2, 3]), dict(citizen_id=2, relatives=[1]), dict(citizen_id=3, relatives=[1]),],
    ),
    # Выгрузка с максимально длинными/большими значениями.
    (
        generate_citizens,
        [
            dict(
                citizens_num=10000,
                relations_num=1000,
                start_citizen_id=MAX_INT - 10000,
                gender="female",
                name=LONGEST_STR,
                town=LONGEST_STR,
                street=LONGEST_STR,
                building=LONGEST_STR,
                apartment=MAX_INT,
            ),
        ],
    ),
    # Житель сам себе родственник.
    # Обработчик должен позволять создавать такие родственные связи.
    (
        generate_citizen,
        [dict(citizen_id=1, name="Джейн", gender="male", birth_date="1945-09-13", town="Нью-Йорк", relatives=[1]),],
    ),
    # Пустая выгрузка
    # Обработчик не должен падать на таких данных.
    (None, [],),
    # Дата рождения - текущая дата
    (generate_citizen, [dict(birth_date=(date.today()).strftime("%Y-%m-%d"))],),
]

WRONG_CASES = [
    # Дата рождения некорректная (в будущем)
    (generate_citizen, [dict(birth_date=(date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))],),
    # citizen_id не уникален в рамках выгрузки
    (generate_citizen, [dict(citizen_id=1), dict(citizen_id=1),],),
    # Родственная связь указана неверно (нет обратной)
    (generate_citizen, [dict(citizen_id=1, relatives=[2]), dict(citizen_id=2, relatives=[]),],),
    # Родственная связь c несуществующим жителем
    (generate_citizen, [dict(citizen_id=1, relatives=[3])],),
    # Родственные связи не уникальны
    (generate_citizen, [dict(citizen_id=1, relatives=[2]), dict(citizen_id=2, relatives=[1, 1])],),
]


def get_citizens_from_case(case: Case) -> List[Dict[str, Any]]:
    func, kwargs_list = case
    if func is None:
        return kwargs_list
    else:
        citizens = []
        if func == generate_citizen:
            citizens = [func(**kwargs) for kwargs in kwargs_list]
        if func == generate_citizens:
            for kwargs in kwargs_list:
                citizens.extend(func(**kwargs))
    return citizens


async def _test_import(database, case):
    citizens = get_citizens_from_case(case)
    import_obj = Import(data=citizens)
    async with database:
        import_id = await analyzer.save_import(import_obj=import_obj, database=database)
        imported_citizens = await analyzer.get_citizens(import_id=import_id, database=database)
    for citizen in imported_citizens:
        del citizen["import_id"]
    assert compare_citizen_groups(citizens, imported_citizens)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CORRECT_CASES)
async def test_correct_imports(migrated_postgres, database, case):
    await _test_import(database, case)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", WRONG_CASES)
async def test_wrong_imports(migrated_postgres, database, case):
    with pytest.raises(ValueError):
        await _test_import(database, case)
