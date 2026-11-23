"""Phân loại lỗi (Blueprint Mục 13.1)."""


class StockAIError(Exception):
    code = "ERROR"

    def __init__(self, message: str, *, code: str | None = None, hint: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.hint = hint

    def to_dict(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "hint": self.hint}}


class TransientError(StockAIError):
    code = "TRANSIENT"


class ConfigError(StockAIError):
    code = "CONFIG"


class ProviderError(StockAIError):
    code = "PROVIDER"


class ValidationError(StockAIError):
    code = "VALIDATION"


class JobCancelled(StockAIError):
    code = "CANCELLED"
