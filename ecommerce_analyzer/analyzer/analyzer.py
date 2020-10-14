"""Analyzer class implements database CRUD operations and high-level business logic."""
from __future__ import annotations

from typing import List, Union

from aiomisc import chunk_list
from api.scheme import CitizenPatch, Import
from databases import Database
from db import citizens, imports, relations
from db.settings import MAX_QUERY_ARGS
from sqlalchemy import Integer, and_, cast, func, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import select


def make_citizens_rows(import_obj: Import, import_id: int) -> List[dict]:
    """Generate ready for insert citizens objects."""
    for citizen in import_obj.data:
        citizen_obj = citizen.dict(exclude_none=True)
        del citizen_obj["relatives"]
        citizen_obj["import_id"] = import_id
        yield citizen_obj


def make_relations_rows(import_obj: Import, import_id: int) -> List[dict]:
    """Generate ready for insert relations objects."""
    for citizen in import_obj.data:
        for relative in citizen.relatives:
            relation_obj = dict(import_id=import_id, citizen=citizen.citizen_id, relative=relative)
            yield relation_obj


async def save_import(import_obj: Import, database: Database) -> Union[int, None]:
    """Create import and corresponding citizens and relations."""
    async with database.transaction():
        insert_import_query = imports.insert().values().returning(imports.c.import_id)
        import_id = await database.fetch_val(insert_import_query)

        if import_obj:

            max_citizens_per_insert = MAX_QUERY_ARGS // len(citizens.columns)
            citizens_rows = make_citizens_rows(import_obj, import_id)
            chunked_citizens = chunk_list(citizens_rows, max_citizens_per_insert)
            insert_citizens_query = citizens.insert()
            for chunk in chunked_citizens:
                await database.execute(insert_citizens_query.values(list(chunk)))

            max_relations_per_insert = MAX_QUERY_ARGS // len(relations.columns)
            relations_rows = make_relations_rows(import_obj, import_id)
            chunked_relations = chunk_list(relations_rows, max_relations_per_insert)
            insert_relations_query = relations.insert()
            for chunk in chunked_relations:
                await database.execute(insert_relations_query.values(list(chunk)))

    return import_id


async def get_citizens(import_id: int, database: Database) -> List[dict]:
    """Get all citizens from particular import."""
    agg_relatives = func.array_remove(func.array_agg(relations.c.relative, type_=ARRAY(Integer)), None).label(
        "relatives"
    )
    query = (
        select([citizens, agg_relatives])
        .select_from(
            citizens.outerjoin(
                relations,
                and_(relations.c.import_id == citizens.c.import_id, relations.c.citizen == citizens.c.citizen_id),
            )
        )
        .where(citizens.c.import_id == import_id)
        .group_by(citizens.c.import_id, citizens.c.citizen_id)
    )
    rows = await database.fetch_all(query)
    result = []
    for row in rows:
        result.append(dict(row))
    return result


async def _get_citizen(import_id: int, citizen_id: int, database: Database) -> dict:
    """Get one citizen from particular import."""
    agg_relatives = func.array_remove(func.array_agg(relations.c.relative, type_=ARRAY(Integer)), None).label(
        "relatives"
    )
    query = (
        select([citizens, agg_relatives])
        .select_from(
            citizens.outerjoin(
                relations,
                and_(citizens.c.import_id == relations.c.import_id, citizens.c.citizen_id == relations.c.citizen),
            )
        )
        .where(and_(citizens.c.citizen_id == citizen_id, citizens.c.import_id == import_id))
        .group_by(citizens.c.import_id, citizens.c.citizen_id)
    )
    row = await database.fetch_one(query)
    return dict(row)


async def _add_relatives(import_id: int, citizen_id: int, relatives: List[int], database: Database) -> None:
    relations_rows = []
    for relative in relatives:
        relations_rows.append(dict(import_id=import_id, citizen=citizen_id, relative=relative))
        if relative != citizen_id:
            relations_rows.append(dict(import_id=import_id, citizen=relative, relative=citizen_id))
    try:
        query = relations.insert().values(relations_rows)
        await database.execute(query)
    except IntegrityError:
        raise ValueError("Can't save relatives, some of provided relatives don't exists")


async def _remove_relatives(import_id: int, citizen_id: int, relatives: List[int], database: Database) -> None:
    for relative in relatives:
        query = relations.delete().where(
            or_(
                and_(
                    relations.c.import_id == import_id,
                    relations.c.citizen == citizen_id,
                    relations.c.relative == relative,
                ),
                and_(
                    relations.c.import_id == import_id,
                    relations.c.citizen == relative,
                    relations.c.relative == citizen_id,
                ),
            )
        )
        await database.execute(query)


async def _update_citizen(import_id: int, citizen_id: int, citizen_patch: CitizenPatch, database: Database) -> None:
    new_citizen_data = citizen_patch.dict(exclude_none=True)
    try:
        new_citizen_data.pop("relatives")
    except KeyError:
        pass
    if len(new_citizen_data) > 0:
        query = (
            citizens.update()
            .where(and_(citizens.c.import_id == import_id, citizens.c.citizen_id == citizen_id))
            .values(new_citizen_data)
        )
        await database.execute(query)


async def patch_citizen(import_id: int, citizen_id: int, citizen_patch: CitizenPatch, database: Database) -> dict:
    """Update citizen."""
    async with database.transaction():
        await _update_citizen(import_id, citizen_id, citizen_patch, database)

        if isinstance(citizen_patch.relatives, list):
            curr_relatives_query = select([relations]).where(
                and_(relations.c.import_id == import_id, relations.c.citizen == citizen_id)
            )
            current_relatives = await database.fetch_all(curr_relatives_query)
            current_relatives = [r["relative"] for r in current_relatives]
            relatives_to_add = [r for r in citizen_patch.relatives if r not in current_relatives]
            if relatives_to_add:
                await _add_relatives(import_id, citizen_id, relatives_to_add, database)

            relatives_to_remove = [r for r in current_relatives if r not in citizen_patch.relatives]
            if relatives_to_remove:
                await _remove_relatives(import_id, citizen_id, relatives_to_remove, database)

    citizen = await _get_citizen(import_id=import_id, citizen_id=citizen_id, database=database)
    return citizen


async def get_birthdays(import_id: int, database: Database) -> dict:
    """Get number of birthdays by every month for particular import."""
    agg_presents = func.count(relations.c.relative).label("presents")

    month = func.date_part("month", citizens.c.birth_date)
    month = cast(month, Integer).label("month")

    query = (
        select([month, relations.c.citizen.label("citizen_id"), agg_presents])
        .select_from(
            citizens.join(
                relations,
                and_(relations.c.import_id == citizens.c.import_id, relations.c.relative == citizens.c.citizen_id,),
            )
        )
        .where(relations.c.import_id == import_id)
        .group_by(month, relations.c.citizen,)
    )
    res = {str(i): [] for i in range(1, 13)}
    async for row in database.iterate(query):
        month = str(row[0])
        res[month].append({"citizen_id": row[1], "presents": row[2]})
    return res


async def get_age_statistics(import_id: int, database: Database) -> List[dict]:
    """Get age percentiles by each town."""
    age = func.date_part("year", func.age(citizens.c.birth_date)).label("age")
    query = (
        select(
            [
                citizens.c.town,
                func.percentile_cont(0.5).within_group(age).label("p50"),
                func.percentile_cont(0.75).within_group(age).label("p75"),
                func.percentile_cont(0.99).within_group(age).label("p99"),
            ]
        )
        .where(citizens.c.import_id == import_id)
        .group_by(citizens.c.town)
    )
    res = []
    async for row in database.iterate(query):
        obj = {
            "town": row[0],
            "p50": row[1],
            "p75": row[2],
            "p99": row[3],
        }
        res.append(obj)
    return res
