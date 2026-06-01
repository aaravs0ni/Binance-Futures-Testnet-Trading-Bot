"""
Tests for configuration module.
Tests environment loading and configuration validation.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from bot.config import Config
from bot import exceptions


class TestConfig:
    """Test configuration management."""
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_key_123',
        'BINANCE_API_SECRET': 'test_secret_456'
    })
    def test_config_loads_from_env(self):
        """Test configuration loads from environment variables."""
        config = Config(env_file=".env.test")
        assert config.get_api_key() == 'test_key_123'
        assert config.get_api_secret() == 'test_secret_456'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_config_missing_api_key(self):
        """Test error when API key is missing."""
        with pytest.raises(exceptions.ConfigurationError) as exc_info:
            Config(env_file=".env.test")
        assert "BINANCE_API_KEY" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_key',
    }, clear=True)
    def test_config_missing_api_secret(self):
        """Test error when API secret is missing."""
        with pytest.raises(exceptions.ConfigurationError) as exc_info:
            Config(env_file=".env.test")
        assert "BINANCE_API_SECRET" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_key_123',
        'BINANCE_API_SECRET': 'test_secret_456',
        'BINANCE_TESTNET_BASE_URL': 'https://custom.binance.com'
    })
    def test_config_custom_url(self):
        """Test configuration with custom Binance URL."""
        config = Config(env_file=".env.test")
        assert config.get_testnet_base_url() == 'https://custom.binance.com'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
