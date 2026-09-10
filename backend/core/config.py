# backend/core/config.py — Quản lý cấu hình & Biến môi trường

import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm file .env trong thư mục gốc của dự án ai-lawyer
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"

if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)
else:
    load_dotenv()

class Settings:
    PROJECT_NAME: str = "Huỳnh Nguyên Khang - Cố Vấn Pháp Lý Trí Tuệ Nhân Tạo"
    VERSION: str = "1.0.0"
    
    # Khóa bí mật & Cấu hình Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    
    # Server host & port
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Thư mục gốc & Thư mục static
    ROOT_DIR: Path = PROJECT_ROOT
    FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"

settings = Settings()
