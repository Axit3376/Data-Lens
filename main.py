from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers.feature_engineering_router import router as feature_engineering_router
from routers.statistics_router import router as statistics_router
from routers.quality_router import router as quality_router
from routers.profiling_router import router as profiling_router
from routers.visualization_router import router as visualization_router
from routers.report_router import router as report_router

app = FastAPI()
app.mount("/static/plots", StaticFiles(directory="plots"), name="static-plots")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(profiling_router)
app.include_router(quality_router)
app.include_router(statistics_router)
app.include_router(feature_engineering_router)
app.include_router(visualization_router)
app.include_router(report_router)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )



