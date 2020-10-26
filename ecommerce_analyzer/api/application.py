"""API service."""
from __future__ import annotations

import os
from typing import Dict, Union

import analyzer
from databases import Database
from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette_prometheus import PrometheusMiddleware, metrics

from .dependencies import database
from .scheme import Citizen, CitizenPatch, Import, Percentiles, Presents, SavedImport

app = FastAPI(title="Ecommerce Analyzer", version="1.0", description="Provides analytical information about citizens")
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)


def get_db() -> Database:
    """Get database."""
    return database


@app.on_event("startup")
async def startup_event() -> None:
    """Start connection pool and clear environment variables on application startup."""
    print(f"Creating connection pool to {database.url}")
    os.environ.clear()
    await database.connect()


@app.on_event("shutdown")
async def disconnect_from_database() -> None:
    """Close connection pool on application shutdown."""
    await database.disconnect()


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return HTTP_400_BAD_REQUEST if data don't pass validation."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.get("/healthcheck")
def health_check() -> Dict[str, str]:
    """Return 200 if ok."""
    return {"message": "ok"}


@app.post("/imports", response_model=SavedImport, status_code=status.HTTP_201_CREATED)
async def save_import(request: Import, database: Database = Depends(get_db)) -> Union[dict, SavedImport, JSONResponse]:
    """Save import to database."""
    import_id = await analyzer.save_import(request, database)
    response = {"data": {"import_id": import_id}}
    return response


@app.patch("/imports/{import_id}/citizens/{citizen_id}", response_model=Citizen, status_code=200)
async def patch_citizen(
    import_id: int, citizen_id: int, request: CitizenPatch, database: Database = Depends(get_db)
) -> Union[dict, JSONResponse]:
    """Patch citizen."""
    try:
        patched_citizen = await analyzer.patch_citizen(import_id, citizen_id, citizen_patch=request, database=database)
    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": e.errors(), "body": e.json()})
        )
    return patched_citizen


@app.get("/imports/{import_id}/citizens", response_model=Import, status_code=200)
async def get_citizens(import_id: int, database: Database = Depends(get_db)) -> Union[dict, Import]:
    """Get citizen."""
    citizens = await analyzer.get_citizens(import_id, database)
    response = {"data": citizens}
    return response


@app.get("/imports/{import_id}/citizens/birthdays", response_model=Presents, status_code=200)
async def get_number_of_birthdays(import_id: int, database: Database = Depends(get_db)) -> Union[dict, Presents]:
    """Get number of birthdays by months."""
    presents_by_month = await analyzer.get_birthdays(import_id, database)
    response = {"data": presents_by_month}
    return response


@app.get("/imports/{import_id}/towns/stat/percentile/age", response_model=Percentiles, status_code=200)
async def get_age_statistics(import_id: int, database: Database = Depends(get_db)) -> Union[dict, Percentiles]:
    """Get age percentiles by each town."""
    age_stats = await analyzer.get_age_statistics(import_id, database)
    response = {"data": age_stats}
    return response
