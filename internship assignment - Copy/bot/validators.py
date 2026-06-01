"""
Validation module.
Validates all user-provided data before it reaches the trading logic.
Produces meaningful error messages to help users correct their input.
Integrates with exchange information to validate against real Binance constraints.
"""

import re
from typing import Tuple, Optional
from . import exceptions
from .exchange_info import ExchangeInfo


class InputValidator:
    """
    Validates user input for trading operations against format rules and exchange constraints.
    Ensures all parameters meet requirements before processing.
    """
    
    # Valid order sides
    VALID_SIDES = {"BUY", "SELL"}
    
    # Valid order types
    VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
    
    # Binance symbol pattern: uppercase letters followed by optional number
    SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]+USDT$")
    
    def __init__(self, exchange_info: Optional[ExchangeInfo] = None):
        """
        Initialize validator with optional exchange info for constraint validation.
        
        Args:
            exchange_info (Optional[ExchangeInfo]): Exchange info provider for symbol validation.
        """
        self.exchange_info = exchange_info
    
    @staticmethod
    def validate_symbol_format(symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate symbol format only (no exchange existence check).
        
        Args:
            symbol (str): Trading symbol to validate (e.g., 'BTCUSDT').
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not symbol:
            return False, "Symbol cannot be empty"
        
        symbol = symbol.strip().upper()
        
        if len(symbol) < 3:
            return False, "Symbol must be at least 3 characters long"
        
        if not InputValidator.SYMBOL_PATTERN.match(symbol):
            return False, (
                "Symbol must follow Binance naming conventions "
                "(e.g., BTCUSDT, ETHUSDT). "
                "Symbols must be uppercase, alphanumeric, and end with 'USDT'"
            )
        
        return True, None
    
    def validate_symbol(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that trading symbol exists on Binance Futures and is trading.
        
        Args:
            symbol (str): Trading symbol to validate (e.g., 'BTCUSDT').
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # First check format
        is_valid, error = InputValidator.validate_symbol_format(symbol)
        if not is_valid:
            return False, error
        
        symbol = symbol.strip().upper()
        
        # Check if symbol exists on exchange (if exchange info available)
        if self.exchange_info:
            try:
                if not self.exchange_info.symbol_exists(symbol):
                    return False, (
                        f"Symbol '{symbol}' not found on Binance Futures or not currently trading. "
                        f"Please verify the symbol is correct."
                    )
            except Exception as e:
                # If we can't check, allow it to proceed (will fail at API)
                pass
        
        return True, None
    
    @staticmethod
    def validate_side(side: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that side is either BUY or SELL.
        
        Args:
            side (str): Order side ('BUY' or 'SELL').
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not side:
            return False, "Order side cannot be empty"
        
        side_upper = side.strip().upper()
        
        if side_upper not in InputValidator.VALID_SIDES:
            return False, f"Order side must be BUY or SELL, got '{side_upper}'"
        
        return True, None
    
    @staticmethod
    def validate_order_type(order_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that order type is either MARKET or LIMIT.
        
        Args:
            order_type (str): Order type ('MARKET' or 'LIMIT').
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not order_type:
            return False, "Order type cannot be empty"
        
        order_type_upper = order_type.strip().upper()
        
        if order_type_upper not in InputValidator.VALID_ORDER_TYPES:
            return False, f"Order type must be MARKET or LIMIT, got '{order_type_upper}'"
        
        return True, None
    
    @staticmethod
    def validate_quantity(quantity: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that quantity is a valid positive number.
        
        Args:
            quantity (str): Quantity as string.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not quantity:
            return False, "Quantity cannot be empty"
        
        try:
            qty = float(quantity.strip())
            if qty <= 0:
                return False, "Quantity must be a positive number"
            return True, None
        except ValueError:
            return False, f"Quantity must be a valid number, got '{quantity}'"
    
    @staticmethod
    def validate_price(price: str, is_limit_order: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate that price is a valid positive number when required for limit orders.
        
        Args:
            price (str): Price as string (can be empty for market orders).
            is_limit_order (bool): Whether this is a limit order. Defaults to False.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Price is optional for market orders
        if not is_limit_order and not price:
            return True, None
        
        # Price is required for limit orders
        if is_limit_order and not price:
            return False, "Price is required for limit orders"
        
        if not price:
            return True, None
        
        try:
            p = float(price.strip())
            if p <= 0:
                return False, "Price must be a positive number"
            return True, None
        except ValueError:
            return False, f"Price must be a valid number, got '{price}'"
    
    def validate_quantity_with_exchange_rules(
        self,
        symbol: str,
        quantity: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate quantity against Binance Futures exchange rules.
        
        Args:
            symbol (str): Trading symbol.
            quantity (float): Order quantity.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not self.exchange_info:
            return True, None  # No exchange info available
        
        is_valid, error = self.exchange_info.validate_quantity(symbol, quantity)
        if not is_valid:
            raise exceptions.InvalidQuantityError(error)
        
        return True, None
    
    def validate_price_with_exchange_rules(
        self,
        symbol: str,
        price: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate price against Binance Futures exchange rules.
        
        Args:
            symbol (str): Trading symbol.
            price (float): Order price.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not self.exchange_info:
            return True, None  # No exchange info available
        
        is_valid, error = self.exchange_info.validate_price(symbol, price)
        if not is_valid:
            raise exceptions.InvalidPriceError(error)
        
        return True, None
    
    def validate_all_inputs(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str = "",
        check_exchange_rules: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all trading inputs together with optional exchange rule checking.
        
        Args:
            symbol (str): Trading symbol.
            side (str): Order side (BUY/SELL).
            order_type (str): Order type (MARKET/LIMIT).
            quantity (str): Order quantity.
            price (str): Order price (required for LIMIT orders).
            check_exchange_rules (bool): Check against exchange constraints.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        
        Raises:
            ValidationError: If any validation fails.
        """
        # Normalize inputs
        symbol = symbol.strip().upper() if symbol else ""
        side = side.strip().upper() if side else ""
        order_type = order_type.strip().upper() if order_type else ""
        quantity = quantity.strip() if quantity else ""
        price = price.strip() if price else ""
        
        # Validate symbol
        is_valid, error = self.validate_symbol(symbol)
        if not is_valid:
            raise exceptions.InvalidSymbolError(error)
        
        # Validate side
        is_valid, error = InputValidator.validate_side(side)
        if not is_valid:
            raise exceptions.InvalidSideError(error)
        
        # Validate order type
        is_valid, error = InputValidator.validate_order_type(order_type)
        if not is_valid:
            raise exceptions.InvalidOrderTypeError(error)
        
        # Validate quantity format
        is_valid, error = InputValidator.validate_quantity(quantity)
        if not is_valid:
            raise exceptions.InvalidQuantityError(error)
        
        # Validate price format (if limit order)
        is_limit = order_type == "LIMIT"
        is_valid, error = InputValidator.validate_price(price, is_limit)
        if not is_valid:
            raise exceptions.InvalidPriceError(error)
        
        # Check exchange rules if requested
        if check_exchange_rules and self.exchange_info:
            try:
                qty = float(quantity)
                self.validate_quantity_with_exchange_rules(symbol, qty)
                
                if is_limit and price:
                    p = float(price)
                    self.validate_price_with_exchange_rules(symbol, p)
            except exceptions.ValidationError:
                raise
            except Exception as e:
                # Log but don't fail if exchange info check fails
                pass
        
        return True, None
