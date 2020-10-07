from datetime import date, timedelta

import pytest
from ecommerce_analyzer.api.scheme import CitizenPatch, Import
from utils import compare_citizen_groups, compare_citizens, generate_citizen, generate_citizens

datasets = [
    # Житель с несколькими родственниками.
    # Обработчик должен корректно возвращать жителя со всеми родственниками.
    [
        generate_citizen(citizen_id=1, relatives=[2, 3]),
        generate_citizen(citizen_id=2, relatives=[1]),
        generate_citizen(citizen_id=3, relatives=[1]),
    ],
    # Житель без родственников.
    # Поле relatives должно содержать пустой список (может иметь значение
    # [null], которое появляется при агрегации строк с LEFT JOIN).
    [generate_citizen(relatives=[])],
    # Выгрузка с жителем, который сам себе родственник.
    # Обработчик должен возвращать идентификатор жителя в списке родственников.
    [generate_citizen(citizen_id=1, name="Джейн", gender="male", birth_date="2020-02-17", relatives=[1])],
    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    [],
]


@pytest.mark.parametrize("dataset", datasets)
def test_get_citizens(analyzer, migrated_postgres, dataset):
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с
    # одним жителем, чтобы убедиться, что обработчик различает жителей разных
    # выгрузок.
    import_obj = Import(data=dataset)
    import_id = analyzer.save_import(import_obj)

    # Проверяем обработчик на указанных данных
    actual_citizens = analyzer.get_citizens(import_id)
    actual_citizens = [citizen.dict() for citizen in actual_citizens]
    assert compare_citizen_groups(actual_citizens, dataset)


def test_patch_citizen(analyzer, migrated_postgres):
    """
    Проверяет, что данные о жителе и его родственниках успешно обновляются.
    """

    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с
    # тремя жителями и одинаковыми идентификаторами, чтобы убедиться, что
    # обработчик различает жителей разных выгрузок и изменения не затронут
    # жителей другой выгрузки.
    side_dataset = [generate_citizen(citizen_id=1), generate_citizen(citizen_id=2), generate_citizen(citizen_id=3)]
    side_import = Import(data=side_dataset)
    side_dataset_id = analyzer.save_import(side_import)

    # Создаем выгрузку с тремя жителями, два из которых родственники для
    # тестирования изменений.
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
    import_obj = Import(data=dataset)
    import_id = analyzer.save_import(import_obj)

    # Обновляем часть полей о жителе, чтобы убедиться что PATCH позволяет
    # передавать только некоторые поля.
    # Данные меняем сразу в выгрузке, чтобы потом было легче сравнивать.
    dataset[0]["name"] = "Иванова Иванна Ивановна"
    patch = CitizenPatch(name=dataset[0]["name"])
    analyzer.patch_citizen(import_id, dataset[0]["citizen_id"], patch)

    # Обновляем другую часть данных, чтобы проверить что данные обновляются.
    dataset[0]["gender"] = "female"
    dataset[0]["birth_date"] = "2020-02-02"
    dataset[0]["town"] = "Другой город"
    dataset[0]["street"] = "Другая улица"
    dataset[0]["building"] = "Другое строение"
    dataset[0]["apartment"] += 1
    # У жителя #1 одна родственная связь должна исчезнуть (с жителем #2),
    # и одна появиться (с жителем #3).
    dataset[0]["relatives"] = [dataset[2]["citizen_id"]]
    # Родственные связи должны быть двусторонними:
    # - у жителя #2 родственная связь с жителем #1 удаляется
    # - у жителя #3 родственная связь с жителем #1 добавляется.
    dataset[2]["relatives"].append(dataset[0]["citizen_id"])
    dataset[1]["relatives"].remove(dataset[0]["citizen_id"])

    patch = CitizenPatch.parse_obj(
        {
            "gender": dataset[0]["gender"],
            "birth_date": dataset[0]["birth_date"],
            "town": dataset[0]["town"],
            "street": dataset[0]["street"],
            "building": dataset[0]["building"],
            "apartment": dataset[0]["apartment"],
            "relatives": dataset[0]["relatives"],
        }
    )
    actual = analyzer.patch_citizen(import_id, dataset[0]["citizen_id"], patch)

    # Проверяем, что житель корректно обновился
    assert compare_citizens(dataset[0], actual.dict())

    # Проверяем всю выгрузку, чтобы убедиться что родственные связи всех
    # жителей изменились корректно.
    actual_citizens = analyzer.get_citizens(import_id)
    actual_citizens = [citizen.dict() for citizen in actual_citizens]
    assert compare_citizen_groups(actual_citizens, dataset)

    # Проверяем, что изменение жителя в тестируемой выгрузке не испортило
    # данные в дополнительной выгрузке.
    actual_citizens = analyzer.get_citizens(side_dataset_id)
    actual_citizens = [citizen.dict() for citizen in actual_citizens]
    assert compare_citizen_groups(actual_citizens, side_dataset)


def test_patch_self_relative(analyzer, migrated_postgres):
    """
    Проверяем что жителю можно указать себя родственником.
    """
    dataset = [
        generate_citizen(
            citizen_id=1, name="Джейн", gender="male", birth_date="1945-03-13", town="Нью-Йорк", relatives=[]
        ),
    ]
    dataset_import = Import(data=dataset)
    import_id = analyzer.save_import(dataset_import)

    dataset[0]["relatives"] = [dataset[0]["citizen_id"]]
    data = {k: v for k, v in dataset[0].items() if k != "citizen_id"}
    patch = CitizenPatch(**data)
    actual = analyzer.patch_citizen(import_id, dataset[0]["citizen_id"], patch)
    assert compare_citizens(dataset[0], actual.dict())


def test_patch_citizen_birthday_in_future(analyzer, migrated_postgres):
    """
    Сервис должен запрещать устанавливать дату рождения в будущем.
    """
    dataset = generate_citizens(citizens_num=1)
    dataset_import = Import(data=dataset)
    import_id = analyzer.save_import(dataset_import)

    birth_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError):
        patch = CitizenPatch(birth_date=birth_date)
        analyzer.patch_citizen(import_id, dataset[0]["citizen_id"], patch)


def test_patch_citizen_add_nonexistent_relative(analyzer, migrated_postgres):
    """
    Сервис должен запрещать добавлять жителю несуществующего родственника.
    """
    dataset = generate_citizens(citizens_num=1)
    dataset_import = Import(data=dataset)
    import_id = analyzer.save_import(dataset_import)

    patch = CitizenPatch(relatives=[999])
    with pytest.raises(Exception):
        analyzer.patch_citizen(import_id, dataset[0]["citizen_id"], patch)
