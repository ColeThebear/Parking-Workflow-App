from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...services import analytics_service
from ...utils.dependencies import require_operator

router = APIRouter()


@router.get("/chart-data")
def get_chart_data(_: User = Depends(require_operator), db: Session = Depends(get_db)):
    return analytics_service.get_chart_data(db)
