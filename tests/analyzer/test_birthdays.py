from typing import Any, Dict, Mapping

import pytest
from ecommerce_analyzer.api.scheme import Import
from utils import generate_citizen


def make_response(values: Mapping[str, Any] = None) -> Dict[str, list]:
    """
    Генерирует словарь, в котором ключи месяцы, а значения по умолчанию - [].
    Позволяет записать ожидаемый ответ в краткой форме.
    """
    return {str(month): values.get(str(month), []) if values else [] for month in range(1, 13)}


datasets = [
    # Житель, у которого несколько родственников.
    # Обработчик должен корректно показывать сколько подарков приобретет
    # житель #1 своим родственникам в каждом месяце.
    {
        "citizens": [
            generate_citizen(citizen_id=1, birth_date="2019-12-31", relatives=[2, 3]),
            generate_citizen(citizen_id=2, birth_date="2020-02-11", relatives=[1]),
            generate_citizen(citizen_id=3, birth_date="2020-02-17", relatives=[1]),
        ],
        "expected": make_response(
            {
                "2": [{"citizen_id": 1, "presents": 2}],
                "12": [{"citizen_id": 2, "presents": 1}, {"citizen_id": 3, "presents": 1}],
            }
        ),
    },
    # Выгрузка с жителем, который сам себе родственник.
    # Обработчик должен корректно показывать что житель купит себе подарок в
    # месяц своего рождения.
    {
        "citizens": [
            generate_citizen(citizen_id=1, name="Джейн", gender="male", birth_date="2020-02-17", relatives=[1])
        ],
        "expected": make_response({"2": [{"citizen_id": 1, "presents": 1}]}),
    },
    # Житель без родственников.
    # Обработчик не должен учитывать его при расчетах.
    {"citizens": [generate_citizen(relatives=[])], "expected": make_response()},
    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    {"citizens": [], "expected": make_response()},
]


@pytest.mark.parametrize("dataset", datasets)
def test_get_birthdays(analyzer, migrated_postgres, dataset):
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с
    # двумя родственниками, чтобы убедиться, что обработчик различает жителей
    # разных выгрузок.
    import_obj = Import(
        data=[generate_citizen(citizen_id=1, relatives=[2]), generate_citizen(citizen_id=2, relatives=[1])]
    )
    analyzer.save_import(import_obj)

    # Проверяем обработчик на указанных данных
    import_id = analyzer.save_import(Import(data=dataset["citizens"]))
    result = analyzer.get_birthdays(import_id)

    for month in dataset["expected"]:
        actual = {(citizen.citizen_id, citizen.presents) for citizen in getattr(result, month)}
        expected = {(citizen["citizen_id"], citizen["presents"]) for citizen in dataset["expected"][month]}
        assert actual == expected
