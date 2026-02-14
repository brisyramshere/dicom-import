"""
DICOM数据管理系统 - 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.db.database import init_db
from app.api import series

# 创建应用
app = FastAPI(
    title="DICOM数据管理系统",
    description="DICOM序列扫描与管理",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(series.router, prefix="/api", tags=["序列管理"])


@app.on_event("startup")
def startup_event():
    """启动时初始化数据库"""
    # 确保数据目录存在
    os.makedirs("./data", exist_ok=True)
    init_db()
    print("数据库初始化完成")


@app.get("/")
def root():
    return {"message": "DICOM数据管理系统 API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
