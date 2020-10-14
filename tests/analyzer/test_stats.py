from datetime import date, timedelta

import analyzer
import pytest
from api.scheme import Import
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


datasets = [
    # Несколько жителей у которых завтра день рождения.
    # Проверяется что обработчик использует в рассчетах количество полных лет.
    {
        "citizens": [
            generate_citizen(birth_date=age2date(years=10, days=364), town="Москва", citizen_id=1),
            generate_citizen(birth_date=age2date(years=30, days=364), town="Москва", citizen_id=2),
            generate_citizen(birth_date=age2date(years=50, days=364), town="Москва", citizen_id=3),
        ],
        "expected": [{"town": "Москва", "p50": 30.0, "p75": 40.0, "p99": 49.6}],
    },
    # Житель у которого сегодня день рождения.
    # Проверяет краевой случай, возраст жителя у которого сегодня день рождения
    # не должен рассчитаться как на 1 год меньше.
    {
        "citizens": [generate_citizen(birth_date=age2date(years=10), town="Москва")],
        "expected": [{"town": "Москва", "p50": 10.0, "p75": 10.0, "p99": 10.0}],
    },
    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    {"citizens": [], "expected": []},
]


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset", datasets)
async def test_get_ages(database, migrated_postgres, dataset):
    # Перед прогоном каждого теста добавим в БД дополнительную выгрузку с
    # жителем из другого города, чтобы убедиться, что обработчик различает
    # жителей разных выгрузок.
    import_obj = Import(data=[generate_citizen(citizen_id=1, town="Санкт-Петербург")])
    async with database:
        await analyzer.save_import(import_obj, database)
        import_id = await analyzer.save_import(Import(data=dataset["citizens"]), database)
        result = await analyzer.get_age_statistics(import_id, database)

    assert len(dataset["expected"]) == len(result), "Towns number is different"
    actual_towns_map = {town["town"]: town for town in result}

    for town in dataset["expected"]:
        assert town["town"] in actual_towns_map
        actual_town = actual_towns_map[town["town"]]

        for percentile in ["p50", "p75", "p99"]:
            assert town[percentile] == actual_town[percentile], (
                f"{town['town']} {percentile} {actual_town[percentile]} does "
                f"not match expected value {town[percentile]}"
            )
