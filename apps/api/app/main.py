import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pet, auth, rewards, shop, ton, breeding
from app.settings import get_settings
from app.services.notifications import set_bot_token, engagement_notification_worker, stop_engagement_worker
from app.deps.db import AsyncSessionLocal

settings = get_settings()

# Фоновая задача для уведомлений
_notification_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _notification_task
    
    # Initialize notification service with bot token
    if settings.bot_token:
        set_bot_token(settings.bot_token)
        # Запускаем фоновую задачу для рассылки уведомлений
        _notification_task = asyncio.create_task(engagement_notification_worker(AsyncSessionLocal))
    
    yield
    
    # Останавливаем фоновую задачу
    if _notification_task:
        await stop_engagement_worker()
        _notification_task.cancel()
        try:
            await _notification_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="TMA Tamagotchi API", debug=settings.debug, lifespan=lifespan)

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
app.include_router(breeding.router)

# Serve static files (Mini App)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")