from fastapi import FastAPI
from routers.profiling import router as profiling_router

app = FastAPI()

app.include_router(profiling_router)

@app.get("/")
async def home():
    return {"message": "Hello World"}



