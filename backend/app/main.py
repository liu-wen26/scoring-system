from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import os

from app.core.config import settings
from app.core.database import init_db, migrate_db, seed_data
from app.api.v1 import exam, user, scan, answer_card, wrong_question, mark, report

app = FastAPI(
    title=settings.APP_NAME,
    description="基于 OCR 识别的智能阅卷平台",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载本地图片静态目录
uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# 注册路由
app.include_router(exam.router, prefix="/api/v1/exam", tags=["考试管理"])
app.include_router(user.router, prefix="/api/v1/user", tags=["用户管理"])
app.include_router(scan.router, prefix="/api/v1/scan", tags=["扫描上传"])
app.include_router(answer_card.router, prefix="/api/v1/answer-card", tags=["答题卡"])
app.include_router(wrong_question.router, prefix="/api/v1/wrong-question", tags=["错题管理"])
app.include_router(mark.router, prefix="/api/v1/mark", tags=["阅卷管理"])
app.include_router(report.router, prefix="/api/v1/report", tags=["成绩报告"])


@app.get("/")
async def root():
    return {"message": settings.APP_NAME, "version": settings.VERSION}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy"}


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "answer_cards")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.dirname(UPLOAD_DIR)), name="uploads")


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print(f"启动 {settings.APP_NAME} v{settings.VERSION}")
    init_db()
    migrate_db()
    seed_data()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)