from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.report_service import generate_report

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/report", response_class=HTMLResponse)
def report(request: Request):

    data = generate_report()

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "request": request,
            **data
        }
    )