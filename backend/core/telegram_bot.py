# backend/core/telegram_bot.py — Bộ điều hướng tích hợp Telegram Bot Webhook
# Cho phép người dân nhắn tin trực tiếp với AI Luật Sư Huỳnh Nguyên Khang qua ứng dụng Telegram

import os
import logging
import requests
from typing import Dict, Any, Optional
from backend.core.gemini_service import legal_service

logger = logging.getLogger("ai_lawyer.telegram")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

class TelegramBotService:
    @staticmethod
    def is_configured() -> bool:
        return bool(TELEGRAM_BOT_TOKEN)

    @staticmethod
    async def process_telegram_update(update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Tiếp nhận và xử lý sự kiện webhook từ Telegram Bot API.
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.info("Chưa cấu hình TELEGRAM_BOT_TOKEN trong biến môi trường.")
            return None

        message = update_data.get("message") or update_data.get("edited_message")
        if not message:
            return None

        chat_id = message.get("chat", {}).get("id")
        user_text = (message.get("text") or "").strip()
        from_user = message.get("from", {})
        user_name = from_user.get("first_name", "Bạn")

        if not chat_id or not user_text:
            return None

        # Lệnh /start hoặc /help
        if user_text.lower() in ["/start", "/help", "start", "help"]:
            welcome_msg = (
                f"Xin chào {user_name}! Tôi là **Huỳnh Nguyên Khang** — Cố vấn Pháp lý Trí tuệ Nhân tạo.\n\n"
                f"Bản quyền & Người sáng lập: **Bố Bảo**.\n\n"
                f"Tôi có thể hỗ trợ bạn:\n"
                f"1. Giải đáp thắc mắc pháp lý (Đất đai, Hôn nhân, Lao động, Hình sự, Dân sự).\n"
                f"2. Bóc tách rủi ro hợp đồng và tính toán án phí.\n\n"
                f"Hãy gửi câu hỏi hoặc mô tả tình huống pháp lý của bạn ngay tại đây!"
            )
            TelegramBotService.send_telegram_message(chat_id, welcome_msg)
            return {"status": "welcomed", "chat_id": chat_id}

        try:
            # Gửi thông báo đang gõ
            TelegramBotService.send_chat_action(chat_id, "typing")

            # Gọi tư vấn pháp lý từ Gemini Service
            ai_response = await legal_service.consult_legal_matter(
                message=user_text,
                history=[],
                category="Tư vấn Tổng hợp"
            )

            reply_text = ai_response.reply
            if ai_response.citations:
                reply_text += "\n\n📚 *Căn cứ pháp lý chính thống (vbpl.vn):*"
                for c in ai_response.citations[:3]:
                    reply_text += f"\n• {c.article_number}: {c.article_title} ({c.law_name})"

            reply_text += "\n\n⚠️ _Lời nhắc: Thông tin mang tính định hướng tham khảo chuyên môn._"

            TelegramBotService.send_telegram_message(chat_id, reply_text)
            return {"status": "replied", "chat_id": chat_id}

        except Exception as e:
            logger.error(f"Lỗi khi xử lý Telegram message: {str(e)}")
            error_msg = "Hệ thống AI đang bận hoặc gặp sự cố xử lý. Vui lòng thử lại sau giây lát."
            TelegramBotService.send_telegram_message(chat_id, error_msg)
            return {"status": "error", "error": str(e)}

    @staticmethod
    def send_telegram_message(chat_id: int, text: str):
        """Gửi tin nhắn phản hồi tới Telegram chat."""
        if not TELEGRAM_BOT_TOKEN:
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        # Chia nhỏ nếu vượt quá giới hạn 4096 ký tự của Telegram
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            try:
                requests.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": "Markdown"
                    },
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Lỗi gửi tin nhắn Telegram: {e}")

    @staticmethod
    def send_chat_action(chat_id: int, action: str = "typing"):
        """Hiển thị trạng thái đang soạn tin nhắn trên Telegram."""
        if not TELEGRAM_BOT_TOKEN:
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
        try:
            requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=4)
        except Exception:
            pass

telegram_bot = TelegramBotService()
process_telegram_update = TelegramBotService.process_telegram_update

