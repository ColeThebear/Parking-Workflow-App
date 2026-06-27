from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...services import import_service
from ...utils.dependencies import require_operator

router = APIRouter()


@router.post("/import-students")
async def import_students(
    file: UploadFile = File(...),
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    try:
        return import_service.import_students(db, text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import-historic")
async def import_historic_sessions(
    file: UploadFile = File(...),
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    try:
        return import_service.import_historic_sessions(db, text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
