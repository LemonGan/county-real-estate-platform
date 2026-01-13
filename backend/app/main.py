"""
FastAPI应用入口文件
"""
import os
import time
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging

from app.core.config import settings
from app.api.v1 import api_router
from app.core.cache import close_redis_client

# 配置日志
log_handlers = [logging.StreamHandler()]

if settings.LOG_FILE:
    # 确保日志目录存在
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    log_handlers.append(logging.FileHandler(settings.LOG_FILE))

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 配置静态文件服务
# 确保静态文件目录存在
static_dir = Path(settings.STATIC_DIR)
static_dir.mkdir(parents=True, exist_ok=True)

# 挂载上传目录到静态文件服务
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)

# 将uploads目录挂载到/static路径
if upload_dir.exists():
    app.mount("/static", StaticFiles(directory=str(upload_dir)), name="static")
    logger.info(f"静态文件服务已挂载: {upload_dir} -> /static")
else:
    logger.warning(f"上传目录不存在: {upload_dir}")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "county-real-estate-api",
        "version": settings.VERSION,
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "县域房产平台API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/api/v1/posts/public")
async def posts_public():
    """公开文章接口（兼容微信开发者工具调试请求）"""
    return {
        "items": [],
        "total": 0,
        "limit": 10,
        "skip": 0
    }


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"请求: {request.method} {request.url.path} - 客户端: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(
            f"响应: {request.method} {request.url.path} - "
            f"状态码: {response.status_code} - "
            f"耗时: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"请求异常: {request.method} {request.url.path} - "
            f"错误: {str(e)} - "
            f"耗时: {process_time:.3f}s",
            exc_info=True
        )
        raise


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(
        f"未处理的异常: {request.method} {request.url.path} - {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 50001,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else "Internal server error",
            "timestamp": time.time()
        }
    )


# HTTPException处理
from fastapi.exceptions import HTTPException as FastAPIHTTPException

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    """HTTP异常处理器"""
    logger.warning(
        f"HTTP异常: {request.method} {request.url.path} - "
        f"状态码: {exc.status_code} - "
        f"详情: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": time.time()
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("正在关闭应用，清理资源...")
    await close_redis_client()
    logger.info("资源清理完成")
