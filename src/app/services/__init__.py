"""Services package - Business logic layer."""
# Lazy imports to avoid circular dependencies
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .blob_storage_service import LocalBlobStorageService
    from .extraction_service import ResumeExtractionService
    from .gemini_service import GeminiService
    from .voice_service import VoiceOnboardingService


def get_extraction_service():
    """Get the global extraction service instance."""
    from .extraction_service import get_extraction_service as _get
    return _get()


def get_gemini_service():
    """Get the global Gemini service instance."""
    from .gemini_service import get_gemini_service as _get
    return _get()


def get_voice_service():
    """Get the global voice service instance."""
    from .voice_service import get_voice_service as _get
    return _get()


def get_blob_storage_service():
    """Get the global blob storage service instance."""
    from .blob_storage_service import get_blob_storage_service as _get
    return _get()


def get_prompt_session_service():
    """Get the global prompt session service instance."""
    from .prompt_session_service import get_prompt_session_service as _get
    return _get()


__all__ = [
    "get_extraction_service",
    "get_gemini_service",
    "get_voice_service",
    "get_blob_storage_service",
    "get_prompt_session_service",
]
