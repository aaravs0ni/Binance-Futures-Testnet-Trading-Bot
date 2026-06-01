"""
Exchange information and rules module.
Fetches and caches Binance exchange rules, validates against real constraints.
Handles symbol existence, precision rules, quantity/price filters.
"""

from typing import Dict, Any, Optional, List, Tuple
import requests
from functools import lru_cache
from . import exceptions
from .logging_config import get_logger


class ExchangeInfo:
    """Manages Binance exchange information and trading rules."""
    
    def __init__(self, base_url: str):
        """
        Initialize ExchangeInfo.
        
        Args:
            base_url (str): Binance Futures API base URL.
        """
        self.base_url = base_url.rstrip('/')
        self.logger = get_logger()
        self._exchange_info = None
        self._symbols_info = {}
    
    def fetch_exchange_info(self) -> Dict[str, Any]:
        """
        Fetch exchange information from Binance.
        
        Returns:
            Dict[str, Any]: Exchange info including symbols and filters.
        
        Raises:
            ConnectionError: If fetch fails.
        """
        if self._exchange_info is not None:
            return self._exchange_info
        
        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/exchangeInfo",
                timeout=10
            )
            response.raise_for_status()
            self._exchange_info = response.json()
            
            # Cache symbol info
            for symbol_data in self._exchange_info.get('symbols', []):
                symbol = symbol_data.get('symbol')
                if symbol:
                    self._symbols_info[symbol] = symbol_data
            
            self.logger.info(f"Loaded exchange info with {len(self._symbols_info)} symbols")
            return self._exchange_info
        
        except Exception as e:
            self.logger.error(f"Failed to fetch exchange info: {str(e)}")
            raise exceptions.ConnectionError(f"Failed to fetch exchange info: {str(e)}")
    
    def symbol_exists(self, symbol: str) -> bool:
        """
        Check if a symbol exists on Binance Futures.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            bool: True if symbol exists and is trading.
        """
        if not self._symbols_info:
            try:
                self.fetch_exchange_info()
            except:
                # If we can't fetch info, allow validation to pass
                self.logger.warning("Could not verify symbol existence")
                return True
        
        symbol = symbol.upper()
        if symbol not in self._symbols_info:
            return False
        
        symbol_data = self._symbols_info[symbol]
        status = symbol_data.get('status')
        return status == 'TRADING'
    
    def get_symbol_filters(self, symbol: str) -> Dict[str, Any]:
        """
        Get all filters for a symbol.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            Dict[str, Any]: Filter information.
        
        Raises:
            InvalidSymbolError: If symbol not found.
        """
        if not self._symbols_info:
            try:
                self.fetch_exchange_info()
            except:
                return {}
        
        symbol = symbol.upper()
        if symbol not in self._symbols_info:
            raise exceptions.InvalidSymbolError(f"Symbol {symbol} not found on Binance Futures")
        
        symbol_data = self._symbols_info[symbol]
        
        # Organize filters by type
        filters = {}
        for filter_item in symbol_data.get('filters', []):
            filter_type = filter_item.get('filterType')
            filters[filter_type] = filter_item
        
        return filters
    
    def get_quantity_filter(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get quantity filter (LOT_SIZE) for a symbol.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            Optional[Dict]: Quantity filter with minQty, maxQty, stepSize.
        """
        filters = self.get_symbol_filters(symbol)
        return filters.get('LOT_SIZE')
    
    def get_price_filter(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get price filter (PRICE_FILTER) for a symbol.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            Optional[Dict]: Price filter with minPrice, maxPrice, tickSize.
        """
        filters = self.get_symbol_filters(symbol)
        return filters.get('PRICE_FILTER')
    
    def get_min_notional(self, symbol: str) -> Optional[float]:
        """
        Get minimum notional value for a symbol.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            Optional[float]: Minimum notional value in USDT.
        """
        filters = self.get_symbol_filters(symbol)
        min_notional = filters.get('MIN_NOTIONAL')
        if min_notional:
            return float(min_notional.get('notional', 0))
        return None
    
    def validate_quantity(self, symbol: str, quantity: float) -> Tuple[bool, Optional[str]]:
        """
        Validate quantity against exchange rules.
        
        Args:
            symbol (str): Trading symbol.
            quantity (float): Order quantity.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            qty_filter = self.get_quantity_filter(symbol)
            if not qty_filter:
                return True, None
            
            min_qty = float(qty_filter.get('minQty', 0))
            max_qty = float(qty_filter.get('maxQty', float('inf')))
            step_size = float(qty_filter.get('stepSize', 0))
            
            # Check min/max
            if quantity < min_qty:
                return False, f"Quantity {quantity} is below minimum {min_qty}"
            if quantity > max_qty:
                return False, f"Quantity {quantity} exceeds maximum {max_qty}"
            
            # Check step size (precision)
            if step_size > 0:
                multiple = quantity / step_size
              # print("DEBUG")
              # print("quantity =", quantity)
              # print("step_size =", step_size)
              # print("multiple =", multiple)
              # print("difference =", abs(multiple - round(multiple)))
                if abs(multiple - round(multiple)) > 1e-8:  # Allow tiny floating point errors
                    return False, (
                        f"Quantity {quantity} does not match step size {step_size}. "
                        f"Use multiples of {step_size}"
                    )
            
            return True, None
        
        except exceptions.InvalidSymbolError as e:
            return False, str(e)
        except Exception as e:
            self.logger.warning(f"Could not validate quantity: {str(e)}")
            return True, None  # Allow if we can't fetch rules
    
    def validate_price(self, symbol: str, price: float) -> Tuple[bool, Optional[str]]:
        """
        Validate price against exchange rules.
        
        Args:
            symbol (str): Trading symbol.
            price (float): Order price.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            price_filter = self.get_price_filter(symbol)
            if not price_filter:
                return True, None
            
            min_price = float(price_filter.get('minPrice', 0))
            max_price = float(price_filter.get('maxPrice', float('inf')))
            tick_size = float(price_filter.get('tickSize', 0))
            
            # Check min/max
            if price < min_price:
                return False, f"Price {price} is below minimum {min_price}"
            if price > max_price:
                return False, f"Price {price} exceeds maximum {max_price}"
            
            # Check tick size (precision)
            if tick_size > 0:
                multiple = price / tick_size

                if abs(multiple - round(multiple)) > 1e-8:  # Allow tiny floating point errors
                    return False, (
                        f"Price {price} does not match tick size {tick_size}. "
                        f"Use increments of {tick_size}"
                    )
            
            return True, None
        
        except exceptions.InvalidSymbolError as e:
            return False, str(e)
        except Exception as e:
            self.logger.warning(f"Could not validate price: {str(e)}")
            return True, None  # Allow if we can't fetch rules
    
    def get_precision_info(self, symbol: str) -> Tuple[int, int]:
        """
        Get required decimal places for quantity and price.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            Tuple[int, int]: (quantity_decimals, price_decimals)
        """
        try:
            qty_filter = self.get_quantity_filter(symbol)
            price_filter = self.get_price_filter(symbol)
            
            # Calculate decimal places from step sizes
            qty_decimals = 0
            if qty_filter and qty_filter.get('stepSize'):
                step_str = str(qty_filter.get('stepSize'))
                if '.' in step_str:
                    qty_decimals = len(step_str.split('.')[1])
            
            price_decimals = 0
            if price_filter and price_filter.get('tickSize'):
                tick_str = str(price_filter.get('tickSize'))
                if '.' in tick_str:
                    price_decimals = len(tick_str.split('.')[1])
            
            return qty_decimals, price_decimals
        
        except:
            return 8, 8  # Default Binance precision
