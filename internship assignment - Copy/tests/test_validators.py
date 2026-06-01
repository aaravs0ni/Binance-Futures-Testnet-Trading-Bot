"""
Unit tests for validators module.
Tests symbol, side, order type, quantity, and price validation.
"""

import pytest
from bot.validators import InputValidator
from bot.exchange_info import ExchangeInfo
from bot import exceptions


class TestSymbolValidation:
    """Test symbol validation."""
    
    def test_symbol_format_valid(self):
        """Test valid symbol formats."""
        is_valid, error = InputValidator.validate_symbol_format("BTCUSDT")
        assert is_valid is True
        assert error is None
    
    def test_symbol_format_invalid_missing_usdt(self):
        """Test symbol without USDT suffix."""
        is_valid, error = InputValidator.validate_symbol_format("BTC")
        assert is_valid is False
        assert "USDT" in error
    
    def test_symbol_format_empty(self):
        """Test empty symbol."""
        is_valid, error = InputValidator.validate_symbol_format("")
        assert is_valid is False
    
    def test_symbol_format_lowercase(self):
        """Test lowercase symbol is converted."""
        is_valid, error = InputValidator.validate_symbol_format("btcusdt")
        assert is_valid is True


class TestSideValidation:
    """Test order side validation."""
    
    def test_side_buy_valid(self):
        """Test BUY side."""
        is_valid, error = InputValidator.validate_side("BUY")
        assert is_valid is True
        assert error is None
    
    def test_side_sell_valid(self):
        """Test SELL side."""
        is_valid, error = InputValidator.validate_side("SELL")
        assert is_valid is True
        assert error is None
    
    def test_side_invalid(self):
        """Test invalid side."""
        is_valid, error = InputValidator.validate_side("HOLD")
        assert is_valid is False
        assert error is not None


class TestOrderTypeValidation:
    """Test order type validation."""
    
    def test_order_type_market_valid(self):
        """Test MARKET type."""
        is_valid, error = InputValidator.validate_order_type("MARKET")
        assert is_valid is True
        assert error is None
    
    def test_order_type_limit_valid(self):
        """Test LIMIT type."""
        is_valid, error = InputValidator.validate_order_type("LIMIT")
        assert is_valid is True
        assert error is None
    
    def test_order_type_invalid(self):
        """Test invalid order type."""
        is_valid, error = InputValidator.validate_order_type("STOP")
        assert is_valid is False


class TestQuantityValidation:
    """Test quantity validation."""
    
    def test_quantity_valid_integer(self):
        """Test valid integer quantity."""
        is_valid, error = InputValidator.validate_quantity("1")
        assert is_valid is True
        assert error is None
    
    def test_quantity_valid_decimal(self):
        """Test valid decimal quantity."""
        is_valid, error = InputValidator.validate_quantity("0.5")
        assert is_valid is True
        assert error is None
    
    def test_quantity_zero(self):
        """Test zero quantity."""
        is_valid, error = InputValidator.validate_quantity("0")
        assert is_valid is False
    
    def test_quantity_negative(self):
        """Test negative quantity."""
        is_valid, error = InputValidator.validate_quantity("-1")
        assert is_valid is False


class TestPriceValidation:
    """Test price validation."""
    
    def test_price_limit_order_required(self):
        """Test price is required for limit orders."""
        is_valid, error = InputValidator.validate_price("", is_limit_order=True)
        assert is_valid is False
    
    def test_price_limit_order_valid(self):
        """Test valid price for limit order."""
        is_valid, error = InputValidator.validate_price("100.5", is_limit_order=True)
        assert is_valid is True
        assert error is None
    
    def test_price_market_order_optional(self):
        """Test price is optional for market orders."""
        is_valid, error = InputValidator.validate_price("", is_limit_order=False)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
