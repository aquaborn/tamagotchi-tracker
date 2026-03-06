from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pet, auth, rewards, shop, ton
from app.settings import get_settings

settings = get_settings()

app = FastAPI(title="TMA Tamagotchi API", debug=settings.debug)

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pet.router)
app.include_router(rewards.router)
app.include_router(shop.router)
app.include_router(ton.router)

# Serve static files (Mini App)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")