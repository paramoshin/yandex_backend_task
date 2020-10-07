"""Analyzer class implements database CRUD operations and high-level business logic."""
from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Any, Callable, Iterator, List, Optional, Tuple

from ecommerce_analyzer.api.scheme import Citizen as CitizenAPI
from ecommerce_analyzer.api.scheme import CitizenPatch
from ecommerce_analyzer.api.scheme import Import as ImportAPI
from ecommerce_analyzer.api.scheme import PresentsByMonth, TownPercentiles
from ecommerce_analyzer.db import Base
from ecommerce_analyzer.db import Citizen as CitizenORM
from ecommerce_analyzer.db import Import, Relation
from sqlalchemy import Integer, and_, cast, create_engine, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.query import Query


@contextmanager
def session_scope(Session: sessionmaker) -> Iterator:
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(func: Callable) -> Callable:
    """Provide transactional scope for wrapped function."""

    @wraps(func)
    def wrapper(self: Analyzer, *args: Any, **kwargs: Any) -> Callable:
        if isinstance(kwargs.get("session"), Session):
            return func(self, *args, **kwargs)
        with session_scope(self.session_factory) as session:
            kwargs.update({"session": session})
            return func(self, *args, **kwargs)

    return wrapper


class Analyzer:
    """Implements CRUD operations and high-level business logic."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        """Initialize instance."""
        self.dsn = dsn or f"postgresql://{user}:{password}@{host}:{port}/{database}"
        engine = create_engine(self.dsn)
        self.session_factory = sessionmaker(bind=engine, expire_on_commit=False, autocommit=False)

    def __call__(self) -> Analyzer:
        """Return self to use class instance as FastAPI application dependency."""
        return self

    @staticmethod
    def _add(model: Base, obj: Any, session: Optional[Session] = None) -> Base:
        session.add(obj)
        session.commit()
        return obj

    @staticmethod
    def _query_get(
        model: Base, order_by: Optional[str] = None, desc: bool = True, session: Optional[Session] = None, **kwargs: Any
    ) -> Query:
        query = session.query(model)
        if kwargs:
            query = query.filter_by(**kwargs)
        if order_by:
            order = getattr(model, order_by)
            if desc:
                order = order.desc()
            query = query.order_by(order)
        return query

    def _get_all(
        self,
        model: Base,
        order_by: Optional[str] = None,
        desc: bool = True,
        session: Optional[Session] = None,
        **kwargs: Any,
    ) -> List[Base]:
        query = self._query_get(model, order_by, desc, session=session, **kwargs)
        return query.all()

    @staticmethod
    def _update(model: Base, new_data: dict, session: Optional[Session] = None, **kwargs: Any) -> None:
        session.query(model).filter_by(**kwargs).update(new_data)

    @staticmethod
    def _delete(model: Base, session: Optional[Session] = None, **kwargs: Any) -> None:
        session.query(model).filter_by(**kwargs).delete()

    @staticmethod
    def _obj_to_dict(obj: Base) -> dict:
        d = {}
        for c in obj.__table__.columns:
            value = getattr(obj, c.name)
            if isinstance(value, Enum):
                value = value.value
            d[c.name] = value
        return d

    @staticmethod
    def _parse_import(import_obj: ImportAPI, import_id: int) -> Tuple[List[dict], List[dict]]:
        """Parse import object into citizens and relations."""
        citizens = []
        relations = []
        for citizen in import_obj.data:
            citizen_obj = citizen.dict(exclude_none=True)
            citizen_obj["import_id"] = import_id
            citizens.append(citizen_obj)
            for relative in citizen.relatives:
                relation_obj = dict(import_id=import_id, citizen=citizen.citizen_id, relative=relative)
                relations.append(relation_obj)

        return citizens, relations

    @with_session
    def save_import(self, import_obj: ImportAPI, session: Optional[Session] = None) -> int:
        """Create import and corresponding citizens and relations."""
        import_id = session.execute(Import.__table__.insert().returning(Import.__table__.c.import_id)).first()[0]
        citizens, relations = self._parse_import(import_obj, import_id)
        for citizen in citizens:
            citizen_obj = CitizenORM(
                import_id=citizen["import_id"],
                citizen_id=citizen["citizen_id"],
                town=citizen["town"],
                street=citizen["street"],
                building=citizen["building"],
                apartment=citizen["apartment"],
                name=citizen["name"],
                birth_date=citizen["birth_date"],
                gender=citizen["gender"],
            )
            self._add(CitizenORM, citizen_obj, session=session)
        for relation in relations:
            relation_obj = Relation(
                import_id=relation["import_id"], citizen=relation["citizen"], relative=relation["relative"]
            )
            self._add(Relation, relation_obj, session=session)

        return import_id

    @with_session
    def get_citizens(self, import_id: int, session: Optional[Session] = None) -> List[CitizenAPI]:
        """Get all citizens from particular import."""
        agg_relatives = func.array_remove(
            func.array_agg(Relation.relative, type_=ARRAY(Integer)).label("relatives"), None
        )
        query = (
            session.query(CitizenORM, agg_relatives)
            .outerjoin(
                Relation, and_(Relation.import_id == CitizenORM.import_id, Relation.citizen == CitizenORM.citizen_id)
            )
            .filter(CitizenORM.import_id == import_id)
            .group_by(CitizenORM.import_id, CitizenORM.citizen_id)
        )
        rows = query.all()
        result = []
        for row in rows:
            citizen, relatives = row
            citizen = self._obj_to_dict(citizen)
            citizen["relatives"] = relatives
            result.append(CitizenAPI.parse_obj(citizen))
        return result

    @with_session
    def get_citizen(self, import_id: int, citizen_id: int, session: Optional[Session] = None) -> CitizenAPI:
        """Get one citizen from particular import."""
        agg_relatives = func.array_remove(
            func.array_agg(Relation.relative, type_=ARRAY(Integer)).label("relatives"), None
        )
        query = (
            session.query(CitizenORM, agg_relatives)
            .outerjoin(
                Relation, and_(CitizenORM.import_id == Relation.import_id, CitizenORM.citizen_id == Relation.citizen,)
            )
            .filter(CitizenORM.citizen_id == citizen_id, CitizenORM.import_id == import_id)
            .group_by(CitizenORM.import_id, CitizenORM.citizen_id)
        )
        citizen, relatives = query.first()
        citizen = self._obj_to_dict(citizen)
        citizen["relatives"] = relatives
        return CitizenAPI.parse_obj(citizen)

    @staticmethod
    def _add_relatives(
        import_id: int, citizen_id: int, relatives: List[int], session: Optional[Session] = None
    ) -> None:
        relative_objs = []
        for relative in relatives:
            relative_objs.append(Relation(import_id=import_id, citizen=citizen_id, relative=relative))
            if relative != citizen_id:
                relative_objs.append(Relation(import_id=import_id, citizen=relative, relative=citizen_id))
        try:
            session.bulk_save_objects(relative_objs)
        except IntegrityError:
            raise ValueError("Can't save relatives, some of provided relatives don't exists")

    def _remove_relatives(
        self, import_id: int, citizen_id: int, relatives: List[int], session: Optional[Session] = None
    ) -> None:
        for relative in relatives:
            print(relative)
            self._delete(Relation, session=session, import_id=import_id, citizen=citizen_id, relative=relative)
            self._delete(Relation, session=session, import_id=import_id, citizen=relative, relative=citizen_id)

    def _update_citizen(
        self, import_id: int, citizen_id: int, citizen_patch: CitizenPatch, session: Optional[Session] = None
    ) -> None:
        new_citizen_data = citizen_patch.dict(exclude_none=True)
        try:
            new_citizen_data.pop("relatives")
        except KeyError:
            pass
        if len(new_citizen_data) > 0:
            self._update(CitizenORM, new_citizen_data, import_id=import_id, citizen_id=citizen_id, session=session)

    @with_session
    def patch_citizen(
        self, import_id: int, citizen_id: int, citizen_patch: CitizenPatch, session: Optional[Session] = None
    ) -> CitizenAPI:
        """Update citizen."""
        self._update_citizen(import_id, citizen_id, citizen_patch, session)
        if isinstance(citizen_patch.relatives, list):
            current_relatives = self._get_all(
                Relation.relative, import_id=import_id, citizen=citizen_id, session=session
            )

            relatives_to_add = [r for r in citizen_patch.relatives if r not in current_relatives]
            self._add_relatives(import_id, citizen_id, relatives_to_add, session)
            session.commit()

            relatives_to_remove = [r[0] for r in current_relatives if r not in citizen_patch.relatives]
            self._remove_relatives(import_id, citizen_id, relatives_to_remove, session)
            session.flush()

        return self.get_citizen(import_id=import_id, citizen_id=citizen_id, session=session)

    @with_session
    def get_birthdays(self, import_id: int, session: Optional[Session] = None) -> PresentsByMonth:
        """Get number of birthdays by every month for particular import."""
        agg_presents = func.count(Relation.relative).label("presents")

        month = func.date_part("month", CitizenORM.birth_date)
        month = cast(month, Integer).label("month")

        query = (
            session.query(month, Relation.citizen.label("citizen_id"), agg_presents,)
            .join(
                CitizenORM,
                and_(Relation.import_id == CitizenORM.import_id, Relation.relative == CitizenORM.citizen_id,),
            )
            .filter(Relation.import_id == import_id)
            .group_by(month, Relation.citizen,)
        )
        rows = query.all()
        res = {str(i): [] for i in range(1, 13)}
        for row in rows:
            month = str(row[0])
            res[month].append({"citizen_id": row[1], "presents": row[2]})
        return PresentsByMonth.parse_obj(res)

    @with_session
    def get_age_statistics(self, import_id: int, session: Optional[Session] = None) -> List[TownPercentiles]:
        """Get age percentiles by each town."""
        age = func.date_part("year", func.age(CitizenORM.birth_date)).label("age")
        query = (
            session.query(
                CitizenORM.town,
                func.percentile_cont(0.5).within_group(age).label("p50"),
                func.percentile_cont(0.75).within_group(age).label("p75"),
                func.percentile_cont(0.99).within_group(age).label("p99"),
            )
            .filter(CitizenORM.import_id == import_id)
            .group_by(CitizenORM.town)
        )
        rows = query.all()
        res = []
        for row in rows:
            obj = {
                "town": row[0],
                "p50": row[1],
                "p75": row[2],
                "p99": row[3],
            }
            res.append(TownPercentiles.parse_obj(obj))
        return res
