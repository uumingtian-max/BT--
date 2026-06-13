from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_chat import router as chat_router
from .routes_extra import router as extra_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(False)
    yield

app = FastAPI(title='乡村振兴聊天 App 后端', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(extra_router)

@app.get('/health')
def health():
    return {'ok': True, 'service': 'rural-revitalization-app'}
