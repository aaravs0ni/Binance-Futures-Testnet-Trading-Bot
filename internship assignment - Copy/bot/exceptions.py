"""
Custom exception classes for the trading bot.
Provides specific exception types for different failure scenarios.
"""


class TradingBotException(Exception):
    """Base exception class for all trading bot errors."""
    pass


class ConfigurationError(TradingBotException):
    """Raised when configuration is invalid or missing required settings."""
    pass


class ValidationError(TradingBotException):
    """Raised when user input validation fails."""
    pass


class AuthenticationError(TradingBotException):
    """Raised when API authentication fails."""
    pass


class ConnectionError(TradingBotException):
    """Raised when there are network/connection issues with Binance."""
    pass


class OrderPlacementError(TradingBotException):
    """Raised when an order placement request fails."""
    pass


class InvalidOrderTypeError(ValidationError):
    """Raised when an invalid order type is specified."""
    pass


class InvalidSideError(ValidationError):
    """Raised when an invalid order side is specified."""
    pass


class InvalidSymbolError(ValidationError):
    """Raised when an invalid trading symbol is specified."""
    pass


class InvalidQuantityError(ValidationError):
    """Raised when quantity is invalid."""
    pass


class InvalidPriceError(ValidationError):
    """Raised when price is invalid."""
    pass


class RateLimitError(TradingBotException):
    """Raised when API rate limit is exceeded."""
    pass
