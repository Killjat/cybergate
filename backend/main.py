"""
账号管理系统 - 后端主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import accounts, scripts, audit, auto_login, auth, users
from database import engine
from models import Base

# 创建所有表（包括新增的 users, user_account_access）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CyberGate", version="2.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(auto_login.router, prefix="/api", tags=["login"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "CyberGate API v2.0"}

if __name__ == "__main__":
    import uvicorn, asyncio

    async def _run():
        config = uvicorn.Config(app, host="0.0.0.0", port=8080)
        server = uvicorn.Server(config)
        await server.serve()

    asyncio.run(_run())
