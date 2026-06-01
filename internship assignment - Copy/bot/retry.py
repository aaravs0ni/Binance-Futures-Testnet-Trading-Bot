"""
Retry mechanism with exponential backoff.
Handles transient failures intelligently with configurable retry strategies.
"""

import time
import random
from typing import Callable, Any, TypeVar, Optional, Type
from . import exceptions

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries (int): Maximum number of retry attempts.
            initial_delay (float): Initial delay in seconds.
            max_delay (float): Maximum delay in seconds.
            exponential_base (float): Base for exponential backoff.
            jitter (bool): Whether to add random jitter to delays.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt (int): Attempt number (0-indexed).
        
        Returns:
            float: Delay in seconds.
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add jitter: ±10% of calculated delay
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class RetryableError(Exception):
    """Indicates an error that can be retried."""
    pass


def is_retryable(exception: Exception) -> bool:
    """
    Determine if an exception represents a transient failure that can be retried.
    
    Args:
        exception (Exception): Exception to check.
    
    Returns:
        bool: True if the exception is transient and can be retried.
    """
    # Network/connection errors are transient
    if isinstance(exception, exceptions.ConnectionError):
        return True
    
    # Rate limit errors are transient (should back off)
    if isinstance(exception, exceptions.RateLimitError):
        return True
    
    # Request timeouts are transient
    if "timeout" in str(exception).lower():
        return True
    
    # Temporary service errors (5xx) are transient
    if "500" in str(exception) or "503" in str(exception):
        return True
    
    return False


def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    logger: Optional[Any] = None,
    **kwargs
) -> T:
    """
    Execute a function with exponential backoff retry strategy.
    
    Args:
        func (Callable): Function to retry.
        *args: Positional arguments for function.
        config (Optional[RetryConfig]): Retry configuration.
        logger (Optional): Logger for retry attempts.
        **kwargs: Keyword arguments for function.
    
    Returns:
        T: Function result.
    
    Raises:
        Exception: Original exception if all retries exhausted.
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        
        except Exception as e:
            last_exception = e
            
            # If not retryable or last attempt, raise immediately
            if not is_retryable(e) or attempt >= config.max_retries:
                raise
            
            # Calculate delay and log
            delay = config.get_delay(attempt)
            if logger:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{config.max_retries + 1}): "
                    f"{str(e)}. Retrying in {delay:.2f}s..."
                )
            
            # Wait before retry
            time.sleep(delay)
    
    # Should not reach here
    raise last_exception


def classify_api_error(status_code: int, error_message: str) -> Type[exceptions.TradingBotException]:
    """
    Classify an API error as permanent or transient.
    
    Args:
        status_code (int): HTTP status code.
        error_message (str): Error message.
    
    Returns:
        Type[exceptions.TradingBotException]: Exception class representing the error type.
    """
    # 4xx errors (except 429) are usually permanent
    if 400 <= status_code < 429:
        return exceptions.OrderPlacementError
    
    # 429 is rate limit (transient)
    if status_code == 429:
        return exceptions.RateLimitError
    
    # 401/403 are authentication (permanent)
    if status_code in (401, 403):
        return exceptions.AuthenticationError
    
    # 5xx errors are usually transient
    if status_code >= 500:
        return exceptions.ConnectionError
    
    # Default to transient
    return exceptions.ConnectionError
