class CRMError(Exception):
    """Domain-level error surfaced to API handlers."""


class AIConfigurationError(CRMError):
    """Raised when AI provider configuration is incomplete."""


class AIProviderError(CRMError):
    """Raised when the AI provider fails after retries."""


class AIResponseValidationError(CRMError):
    """Raised when an AI response cannot be parsed or validated."""
