"""API service."""
from typing import List, Union

from ecommerce_analyzer.analyzer import Analyzer
from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, PositiveInt, ValidationError

from .scheme import Citizen, CitizenPatch, Import, PresentsByMonth, TownPercentiles
from .settings import analyzer

app = FastAPI(title="Ecommerce Analyzer", version="1.0", description="Provides analytical information about citizens")


class ImportId(BaseModel):
    """Import id."""

    import_id: PositiveInt


class SavedImport(BaseModel):
    """Saved import."""

    data: ImportId


class Presents(BaseModel):
    """Presents by month."""

    data: PresentsByMonth


class Percentiles(BaseModel):
    """Age percentiles."""

    data: List[TownPercentiles]


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return HTTP_400_BAD_REQUEST if data don't pass validation."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.post("/imports", response_model=SavedImport, status_code=status.HTTP_201_CREATED)
def save_import(request: Import, analyzer: Analyzer = Depends(analyzer)) -> SavedImport:
    """Save import to database."""
    import_id = analyzer.save_import(request)
    response = {"data": {"import_id": import_id}}
    return SavedImport.parse_obj(response)


@app.patch("/imports/{import_id}/citizens/{citizen_id}", response_model=Citizen, status_code=200)
def patch_citizen(
    import_id: int, citizen_id: int, request: CitizenPatch, analyzer: Analyzer = Depends(analyzer)
) -> Union[Citizen, JSONResponse]:
    """Patch citizen."""
    try:
        patched_citizen = analyzer.patch_citizen(import_id, citizen_id, citizen_patch=request)
    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": e.errors(), "body": e.json()})
        )
    return patched_citizen


@app.get("/imports/{import_id}/citizens", response_model=Import, status_code=200)
def get_citizens(import_id: int, analyzer: Analyzer = Depends(analyzer)) -> Import:
    """Get citizen."""
    citizens = analyzer.get_citizens(import_id)
    response = {"data": citizens}
    return Import.parse_obj(response)


@app.get("/imports/{import_id}/citizens/birthdays", response_model=Presents, status_code=200)
def get_number_of_birthdays(import_id: int, analyzer: Analyzer = Depends(analyzer)) -> Presents:
    """Get number of birthdays by months."""
    presents_by_month = analyzer.get_birthdays(import_id)
    response = {"data": presents_by_month}
    return Presents.parse_obj(response)


@app.get("/imports/{import_id}/towns/stat/percentile/age", response_model=Percentiles, status_code=200)
def get_age_statistics(import_id: int, analyzer: Analyzer = Depends(analyzer)) -> Percentiles:
    """Get age percentiles by each town."""
    age_stats = analyzer.get_age_statistics(import_id)
    response = {"data": age_stats}
    return Percentiles.parse_obj(response)
