from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.redis import init_redis, close_redis
from app.api import auth, info, shop, wallet, neighbors, admin, pets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(title="DF Token Bot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth ПЕРВЫМ — остальные роутеры зависят от него
app.include_router(auth.router, prefix="/api")
app.include_router(info.router, prefix="/api")
app.include_router(shop.router, prefix="/api")
app.include_router(wallet.router, prefix="/api")
app.include_router(neighbors.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(pets.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
