from fastapi import FastAPI

from routers.feature_engineering_router import router as feature_engineering_router
from routers.statistics_router import router as statistics_router
from routers.quality_router import router as quality_router
from routers.profiling_router import router as profiling_router

app = FastAPI()

app.include_router(profiling_router)
app.include_router(quality_router)
app.include_router(statistics_router)
app.include_router(feature_engineering_router)

@app.get("/")
async def home():
    return {"message": "Welcome to Data Lens!"}



