"""
Configuration module.
Loads environment variables, validates configuration, and provides centralized access to settings.
Includes enhanced secret handling and permission verification.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from . import exceptions


class Config:
    """
    Configuration manager for the trading bot.
    Loads and validates environment variables, storing configuration values.
    Implements secure secret handling and startup permission checks.
    """
    
    # Minimum required environment variable
    REQUIRED_KEYS = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
    
    # Optional environment variables with defaults
    OPTIONAL_KEYS = {
        'BINANCE_TESTNET_BASE_URL': 'https://testnet.binancefuture.com',
        'BINANCE_TESTNET_STREAM_URL': 'wss://stream.binancefuture.com'
    }
    
    def __init__(self, env_file: str = ".env", verify_env_file: bool = True):
        """
        Initialize configuration by loading environment variables.
        
        Args:
            env_file (str): Path to the .env file. Defaults to ".env".
            verify_env_file (bool): Verify .env file exists and is not world-readable. Defaults to True.
        
        Raises:
            ConfigurationError: If required configuration is missing or invalid.
        """
        # Verify environment file security if it exists
        if verify_env_file and Path(env_file).exists():
            self._verify_env_file_security(env_file)
        
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        # Load and validate required settings
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.testnet_base_url = os.getenv(
            "BINANCE_TESTNET_BASE_URL",
            self.OPTIONAL_KEYS['BINANCE_TESTNET_BASE_URL']
        )
        self.testnet_stream_url = os.getenv(
            "BINANCE_TESTNET_STREAM_URL",
            self.OPTIONAL_KEYS['BINANCE_TESTNET_STREAM_URL']
        )
        
        # Validate all required settings are available
        self._validate_configuration()
    
    def _verify_env_file_security(self, env_file: str) -> None:
        """
        Verify that the .env file has secure permissions.
        
        Args:
            env_file (str): Path to .env file.
        """
        try:
            env_path = Path(env_file)
            if not env_path.exists():
                return
            
            # Check file permissions (on Unix-like systems)
            import stat
            file_stat = env_path.stat()
            
            # Warn if file is readable by others
            if file_stat.st_mode & stat.S_IROTH:
                logger = logging.getLogger("TradingBot")
                logger.warning(
                    f"WARNING: {env_file} is readable by others. "
                    f"Consider running: chmod 600 {env_file}"
                )
        except Exception:
            pass  # Silently ignore permission check failures
    
    def _validate_configuration(self) -> None:
        """
        Validate that all required configuration settings are available.
        
        Raises:
            ConfigurationError: If any required setting is missing or invalid.
        """
        errors = []
        
        if not self.api_key:
            errors.append("BINANCE_API_KEY is not set in environment variables")

        if not self.api_secret:
            errors.append("BINANCE_API_SECRET is not set in environment variables")
        
        if not self.testnet_base_url:
            errors.append("BINANCE_TESTNET_BASE_URL is not set or invalid")
        
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise exceptions.ConfigurationError(error_message)
    
    def get_api_key(self) -> str:
        """Get the Binance API key (masked in logs)."""
        return self.api_key
    
    def get_api_secret(self) -> str:
        """Get the Binance API secret (masked in logs)."""
        return self.api_secret
    
    def get_testnet_base_url(self) -> str:
        """Get the Binance Futures Testnet base URL."""
        return self.testnet_base_url
    
    def get_testnet_stream_url(self) -> str:
        """Get the Binance Futures Testnet WebSocket stream URL."""
        return self.testnet_stream_url
    
    def is_testnet(self) -> bool:
        """
        Check if this is configured for testnet (always True for this application).
        
        Returns:
            bool: True if testnet URL is being used.
        """
        return 'testnet' in self.testnet_base_url.lower()
    
    def clear_secrets(self) -> None:
        """
        Clear secrets from memory (best-effort).
        This is a security best-practice, though Python may still have references.
        """
        if self.api_key:
            self.api_key = '*' * len(self.api_key)
        if self.api_secret:
            self.api_secret = '*' * len(self.api_secret)
    
    def __repr__(self) -> str:
        """String representation of configuration (without exposing secrets)."""
        return (
            f"Config(api_key=***MASKED***, api_secret=***MASKED***, "
            f"testnet={self.is_testnet()}, "
            f"base_url={self.testnet_base_url})"
        )
    
    def __del__(self):
        """Destructor to attempt secret cleanup."""
        try:
            self.clear_secrets()
        except:
            pass


# Return a fresh configuration instance (avoid global singletons)
def get_config(env_file: str = ".env") -> Config:
    """
    Create and return a new configuration instance.

    Args:
        env_file (str): Path to the .env file.

    Returns:
        Config: A fresh configuration instance.

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    return Config(env_file)


