from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import pet, auth
from app.settings import get_settings

settings = get_settings()

app = FastAPI(title="TMA Tamagotchi API", debug=settings.debug)

app.include_router(auth.router)
app.include_router(pet.router)

# Serve static files (Mini App)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")