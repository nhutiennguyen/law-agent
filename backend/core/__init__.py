from backend.core.config import settings
from backend.core.gemini_service import legal_service
from backend.core.legal_prompts import LEGAL_SYSTEM_INSTRUCTION, SUPPORTED_CATEGORIES, LEGAL_DISCLAIMER

__all__ = ["settings", "legal_service", "LEGAL_SYSTEM_INSTRUCTION", "SUPPORTED_CATEGORIES", "LEGAL_DISCLAIMER"]
