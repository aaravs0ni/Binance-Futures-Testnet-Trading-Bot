"""
Integration tests for the trading bot.
Tests order placement workflows with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bot.client import BinanceClient
from bot.orders import OrderService, OrderResult
from bot import exceptions


class TestOrderService:
    """Test order service functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mocked Binance client."""
        client = Mock(spec=BinanceClient)
        client.get_account_info.return_value = {'canTrade': True, 'availableBalance': 10000}
        client.get_leverage.return_value = 1
        client.get_position_mode.return_value = {'dualSidePosition': False}
        return client
    
    @pytest.fixture
    def order_service(self, mock_client):
        """Create OrderService with mocked client."""
        return OrderService(mock_client)
    
    def test_market_order_success(self, mock_client, order_service):
        """Test successful market order placement."""
        mock_client.place_market_order.return_value = {
            'orderId': 123456,
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'type': 'MARKET',
            'status': 'FILLED',
            'origQty': 0.001,
            'executedQty': 0.001,
            'cumQuote': 45000,
            'fills': [{'price': '45000', 'qty': '0.001', 'commission': '0.0'}]
        }
        
        result = order_service.place_market_order('BTCUSDT', 'BUY', 0.001, check_margin=False, follow_up=False)
        
        assert result.success is True
        assert result.order_id == 123456
        assert result.status == 'FILLED'
        assert result.executed_qty == 0.001
    
    def test_market_order_insufficient_margin(self, mock_client, order_service):
        """Test market order with insufficient margin."""
        mock_client.get_account_info.return_value = {'canTrade': True, 'availableBalance': 1}
        
        result = order_service.place_market_order('BTCUSDT', 'BUY', 10, check_margin=True, follow_up=False)
        
        assert result.success is False
        assert "margin" in result.message.lower()
    
    def test_limit_order_success(self, mock_client, order_service):
        """Test successful limit order placement."""
        mock_client.place_limit_order.return_value = {
            'orderId': 123457,
            'symbol': 'ETHUSDT',
            'side': 'BUY',
            'type': 'LIMIT',
            'status': 'NEW',
            'price': '2500',
            'origQty': 1,
            'executedQty': 0,
            'cumQuote': 0,
            'fills': []
        }
        
        result = order_service.place_limit_order('ETHUSDT', 'BUY', 1, 2500, check_margin=False, follow_up=False)
        
        assert result.success is True
        assert result.order_id == 123457
        assert result.status == 'NEW'
        assert result.executed_qty == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
