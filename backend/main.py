# backend/main.py — Điểm khởi động ứng dụng FastAPI & Mount Frontend

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.config import settings
from backend.api.routes import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Cố vấn Pháp lý Trí tuệ Nhân tạo - Tư vấn Pháp luật Việt Nam chuyên sâu theo quy chuẩn 4 bước",
    version=settings.VERSION
)

# Cấu hình Security Headers chống clickjacking, MIME-sniffing, XSS
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Cấu hình CORS để frontend giao tiếp thông suốt
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký API router
app.include_router(api_router)

# Mount thư mục tĩnh frontend nếu tồn tại
if settings.FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=settings.FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=settings.FRONTEND_DIR / "js"), name="js")
    if (settings.FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=settings.FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        """Phục vụ trang giao diện chính của AI Lawyer."""
        index_file = settings.FRONTEND_DIR / "index.html"
        return FileResponse(index_file)

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Đang khởi động {settings.PROJECT_NAME} tại http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
