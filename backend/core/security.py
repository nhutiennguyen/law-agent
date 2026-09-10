# backend/core/security.py — Bộ lọc bảo mật, Rate Limiting & Xác thực dữ liệu an toàn

import time
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status

logger = logging.getLogger("ai_lawyer.security")

class InMemoryRateLimiter:
    """
    Bộ đếm giới hạn tốc độ (Rate Limiter) theo địa chỉ IP sử dụng thuật toán Sliding Window.
    Nhẹ, thuần Python, không cần cài Redis, bảo vệ chống spam và cạn kiệt Quota.
    """
    def __init__(self, requests_per_minute: int = 25, window_seconds: int = 60):
        self.limit = requests_per_minute
        self.window = window_seconds
        self.ip_history: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup_old_records(self, now: float):
        """Dọn dẹp các bản ghi đã quá hạn để tránh phình bộ nhớ."""
        if now - self._last_cleanup > 300:  # Cứ 5 phút dọn 1 lần
            cutoff = now - self.window
            expired_ips = []
            for ip, timestamps in self.ip_history.items():
                self.ip_history[ip] = [t for t in timestamps if t > cutoff]
                if not self.ip_history[ip]:
                    expired_ips.append(ip)
            for ip in expired_ips:
                del self.ip_history[ip]
            self._last_cleanup = now

    def check_rate_limit(self, request: Request, custom_limit: int = None) -> bool:
        """Kiểm tra tần suất của client IP, ném lỗi 429 nếu vượt ngưỡng."""
        now = time.time()
        self._cleanup_old_records(now)

        # Lấy IP thực tế (hỗ trợ reverse proxy / Cloudflare / Render)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        cutoff = now - self.window
        timestamps = [t for t in self.ip_history[client_ip] if t > cutoff]
        self.ip_history[client_ip] = timestamps

        limit = custom_limit or self.limit
        if len(timestamps) >= limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} ({len(timestamps)}/{limit} req/min)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="⚠️ Bạn đang gửi yêu cầu quá nhanh! Vui lòng đợi 30 giây trước khi thử lại để bảo vệ hệ thống."
            )

        self.ip_history[client_ip].append(now)
        return True

# Khởi tạo các rate limiters dùng chung
chat_limiter = InMemoryRateLimiter(requests_per_minute=25, window_seconds=60)
upload_limiter = InMemoryRateLimiter(requests_per_minute=8, window_seconds=60)

# Cấu hình giới hạn kích thước và định dạng file an toàn
MAX_MESSAGE_LENGTH = 4000
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"}

def validate_message_length(message: str, max_len: int = MAX_MESSAGE_LENGTH):
    """Kiểm tra độ dài tin nhắn chống bom dữ liệu."""
    if len(message) > max_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nội dung câu hỏi quá dài (tối đa {max_len} ký tự). Vui lòng rút ngắn câu hỏi của bạn."
        )

def validate_uploaded_file(filename: str, file_size: int):
    """Kiểm tra file upload chống malware, file thực thi và quá dung lượng."""
    import os
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng file '{ext}' không được hỗ trợ. Vui lòng chỉ tải lên file: PDF, Word (.docx, .doc), TXT hoặc Ảnh scan (.png, .jpg)."
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dung lượng file vượt quá giới hạn cho phép (tối đa 10MB). Vui lòng chọn file nhẹ hơn."
        )
