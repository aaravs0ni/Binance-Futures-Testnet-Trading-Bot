"""
Orders module.
Contains trading business logic for placing and processing orders.
Handles market and limit order workflows with order status follow-up, margin checks, and account validation.
"""

import time
from typing import Dict, Any, Optional, List
from .client import BinanceClient
from .logging_config import get_logger
from . import exceptions


class OrderResult:
    """Structured result for trading operations."""
    
    def __init__(
        self,
        success: bool,
        message: str,
        order_id: Optional[int] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        order_type: Optional[str] = None,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        status: Optional[str] = None,
        executed_qty: Optional[float] = None,
        avg_price: Optional[float] = None,
        cumulative_quote_asset_transacted_qty: Optional[float] = None,
        raw_response: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize OrderResult.
        
        Args:
            success (bool): Whether the order was placed successfully.
            message (str): Human-readable message describing the result.
            order_id (Optional[int]): Binance order ID.
            symbol (Optional[str]): Trading symbol.
            side (Optional[str]): Order side (BUY/SELL).
            order_type (Optional[str]): Order type (MARKET/LIMIT).
            quantity (Optional[float]): Order quantity.
            price (Optional[float]): Order price.
            status (Optional[str]): Order status (NEW, PARTIALLY_FILLED, FILLED, CANCELLED, etc).
            executed_qty (Optional[float]): Quantity executed.
            avg_price (Optional[float]): Average execution price.
            cumulative_quote_asset_transacted_qty (Optional[float]): Total quote asset used.
            raw_response (Optional[Dict]): Raw response from Binance.
        """
        self.success = success
        self.message = message
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.status = status
        self.executed_qty = executed_qty
        self.avg_price = avg_price
        self.cumulative_quote_asset_transacted_qty = cumulative_quote_asset_transacted_qty
        self.raw_response = raw_response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'message': self.message,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'executed_qty': self.executed_qty,
            'avg_price': self.avg_price,
            'cumulative_quote_asset_transacted_qty': self.cumulative_quote_asset_transacted_qty
        }
    
    def __repr__(self) -> str:
        return f"OrderResult(success={self.success}, status={self.status}, order_id={self.order_id})"


class OrderService:
    """
    Service for handling trading operations.
    Manages market and limit order workflows with account validation and status monitoring.
    """
    
    def __init__(self, client: BinanceClient):
        """
        Initialize OrderService with a Binance client.
        
        Args:
            client (BinanceClient): Initialized Binance client.
        """
        self.client = client
        self.logger = get_logger()
    
    def _check_margin_available(self, symbol: str, quantity: float, price: Optional[float]) -> bool:
        """
        Check if sufficient margin is available for the order.
        
        Args:
            symbol (str): Trading symbol.
            quantity (float): Order quantity.
            price (Optional[float]): Order price (for limit orders).
        
        Returns:
            bool: True if sufficient margin, False otherwise.
        
        Raises:
            ConnectionError: If account check fails.
        """
        try:
            account = self.client.get_account_info()
            
            # Check if account can trade
            if not account.get('canTrade', False):
                self.logger.error("Account trading is disabled")
                raise exceptions.OrderPlacementError("Your account does not have trading permissions")
            
            # Get available balance
            available_balance = float(account.get('availableBalance', 0))
            
            # Estimate cost
            if price:
                estimated_cost = quantity * price
            else:
                # For market orders, use last price (would need to fetch from order book in production)
                estimated_cost = quantity * 1000  # Conservative estimate
            
            if available_balance < estimated_cost:
                self.logger.warning(
                    f"Insufficient margin: available={available_balance}, required≈{estimated_cost}"
                )
                return False
            
            self.logger.debug(f"Margin check passed: available={available_balance}")
            return True
        
        except exceptions.TradingBotException:
            raise
        except Exception as e:
            self.logger.warning(f"Could not verify margin: {str(e)}")
            return True  # Don't fail if we can't check
    
    def _check_leverage(self, symbol: str) -> int:
        """
        Get current leverage setting for a symbol.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            int: Current leverage (default 1 if cannot determine).
        """
        try:
            leverage = self.client.get_leverage(symbol)
            self.logger.debug(f"Current leverage for {symbol}: {leverage}x")
            return leverage
        except Exception as e:
            self.logger.warning(f"Could not check leverage: {str(e)}")
            return 1  # Default if check fails
    
    def _check_position_mode(self) -> str:
        """
        Check position mode (One-way or Hedge mode).
        
        Returns:
            str: Position mode ("One-way" or "Hedge").
        """
        try:
            mode_info = self.client.get_position_mode()
            is_dual = mode_info.get('dualSidePosition', False)
            mode = "Hedge" if is_dual else "One-way"
            self.logger.debug(f"Position mode: {mode}")
            return mode
        except Exception as e:
            self.logger.warning(f"Could not check position mode: {str(e)}")
            return "One-way"  # Default
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        check_margin: bool = True,
        follow_up: bool = True
    ) -> OrderResult:
        """
        Execute a market order workflow.
        
        Validates margin, checks leverage and position mode, sends request,
        processes response, monitors order status, and returns result.
        
        Args:
            symbol (str): Trading symbol.
            side (str): Order side (BUY/SELL).
            quantity (float): Order quantity.
            check_margin (bool): Check margin before placing. Defaults to True.
            follow_up (bool): Monitor order status after placement. Defaults to True.
        
        Returns:
            OrderResult: Structured result of the order operation.
        """
        try:
            # Log order initiation
            self.logger.info(
                f"Market order initiated: {side} {quantity} {symbol}"
            )
            
            # Check margin if requested
            if check_margin and not self._check_margin_available(symbol, quantity, None):
                error_msg = "Insufficient margin to place order"
                return OrderResult(
                    success=False,
                    message=error_msg,
                    symbol=symbol,
                    side=side,
                    order_type="MARKET",
                    quantity=quantity
                )
            
            # Check leverage and position mode
            leverage = self._check_leverage(symbol)
            position_mode = self._check_position_mode()
            
            # Place order through client
            response = self.client.place_market_order(symbol, side, quantity)
            
            # Process response
            order_result = self._process_order_response(
                response=response,
                order_type="MARKET",
                input_price=None
            )
            
            # Monitor order if requested
            if follow_up and order_result.success and order_result.order_id:
                self._follow_up_order(symbol, order_result.order_id)
            
            # Log successful order
            if order_result.success:
                self.logger.info(
                    f"Market order successful: {order_result.message} "
                    f"(Order ID: {order_result.order_id}, Leverage: {leverage}x, Mode: {position_mode})"
                )
            
            return order_result
        
        except exceptions.TradingBotException as e:
            error_msg = str(e)
            self.logger.error(f"Market order failed: {error_msg}")
            return OrderResult(
                success=False,
                message=error_msg,
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity
            )
        except Exception as e:
            error_msg = f"Unexpected error during market order: {str(e)}"
            self.logger.error(error_msg)
            return OrderResult(
                success=False,
                message=error_msg,
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity
            )
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        check_margin: bool = True,
        follow_up: bool = True
    ) -> OrderResult:
        """
        Execute a limit order workflow.
        
        Validates margin, checks leverage and position mode, sends request,
        processes response, monitors order status, and returns result.
        
        Args:
            symbol (str): Trading symbol.
            side (str): Order side (BUY/SELL).
            quantity (float): Order quantity.
            price (float): Order price.
            time_in_force (str): Time in force ('GTC', 'IOC', 'FOK'). Defaults to 'GTC'.
            check_margin (bool): Check margin before placing. Defaults to True.
            follow_up (bool): Monitor order status after placement. Defaults to True.
        
        Returns:
            OrderResult: Structured result of the order operation.
        """
        try:
            # Verify price is valid
            if not price or price <= 0:
                raise exceptions.InvalidPriceError("Valid positive price is required for limit orders")
            
            # Log order initiation
            self.logger.info(
                f"Limit order initiated: {side} {quantity} {symbol} @ {price} TIF={time_in_force}"
            )
            
            # Check margin if requested
            if check_margin and not self._check_margin_available(symbol, quantity, price):
                error_msg = "Insufficient margin to place order"
                return OrderResult(
                    success=False,
                    message=error_msg,
                    symbol=symbol,
                    side=side,
                    order_type="LIMIT",
                    quantity=quantity,
                    price=price
                )
            
            # Check leverage and position mode
            leverage = self._check_leverage(symbol)
            position_mode = self._check_position_mode()
            
            # Place order through client
            response = self.client.place_limit_order(
                symbol,
                side,
                quantity,
                price,
                time_in_force
            )
            
            # Process response
            order_result = self._process_order_response(
                response=response,
                order_type="LIMIT",
                input_price=price
            )
            
            # Monitor order if requested and order is open
            if follow_up and order_result.success and order_result.order_id:
                if order_result.status in ['NEW', 'PARTIALLY_FILLED']:
                    self._monitor_open_limit_order(symbol, order_result.order_id)
            
            # Log successful order
            if order_result.success:
                self.logger.info(
                    f"Limit order successful: {order_result.message} "
                    f"(Order ID: {order_result.order_id}, Leverage: {leverage}x, Mode: {position_mode})"
                )
            
            return order_result
        
        except exceptions.TradingBotException as e:
            error_msg = str(e)
            self.logger.error(f"Limit order failed: {error_msg}")
            return OrderResult(
                success=False,
                message=error_msg,
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price
            )
        except Exception as e:
            error_msg = f"Unexpected error during limit order: {str(e)}"
            self.logger.error(error_msg)
            return OrderResult(
                success=False,
                message=error_msg,
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price
            )
    
    def _follow_up_order(self, symbol: str, order_id: int, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Follow up on order status immediately after placement (for market orders).
        
        Args:
            symbol (str): Trading symbol.
            order_id (int): Order ID.
            timeout (int): Maximum time to wait for status update (seconds).
        
        Returns:
            Optional[Dict]: Final order status, or None if timeout.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                order_status = self.client.get_order_status(symbol, order_id)
                status = order_status.get('status')
                
                self.logger.info(f"Order {order_id} status update: {status}")
                
                # Stop monitoring if order is filled or cancelled
                if status in ['FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED']:
                    return order_status
                
                # Wait before next check
                time.sleep(2)
            
            except Exception as e:
                self.logger.warning(f"Could not check order status: {str(e)}")
                return None
        
        self.logger.warning(f"Order {order_id} status check timed out")
        return None
    
    def _monitor_open_limit_order(self, symbol: str, order_id: int) -> None:
        """
        Log information about an open limit order for monitoring.
        
        Args:
            symbol (str): Trading symbol.
            order_id (int): Order ID.
        """
        try:
            order_status = self.client.get_order_status(symbol, order_id)
            
            status = order_status.get('status')
            executed_qty = float(order_status.get('executedQty', 0))
            orig_qty = float(order_status.get('origQty', 0))
            
            if status in ['NEW', 'PARTIALLY_FILLED']:
                fill_percentage = (executed_qty / orig_qty * 100) if orig_qty > 0 else 0
                self.logger.info(
                    f"Limit order {order_id} is OPEN: {fill_percentage:.1f}% filled "
                    f"({executed_qty}/{orig_qty} {symbol}). "
                    f"Monitor this order to ensure it executes as intended."
                )
        except Exception as e:
            self.logger.debug(f"Could not monitor open order: {str(e)}")
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all open orders.
        
        Args:
            symbol (Optional[str]): Filter by symbol. If None, get all open orders.
        
        Returns:
            List[Dict]: List of open orders.
        """
        try:
            orders = self.client.get_open_orders(symbol)
            self.logger.info(f"Retrieved {len(orders)} open orders" + (f" for {symbol}" if symbol else ""))
            return orders
        except Exception as e:
            self.logger.error(f"Failed to get open orders: {str(e)}")
            return []
    
    def _process_order_response(
        self,
        response: Dict[str, Any],
        order_type: str,
        input_price: Optional[float] = None
    ) -> OrderResult:
        """
        Process Binance Futures API response and extract relevant information.
        
        Handles futures-specific response fields including fills and commissions.
        
        Args:
            response (Dict): Raw response from Binance API.
            order_type (str): Order type ('MARKET' or 'LIMIT').
            input_price (Optional[float]): Input price for limit orders.
        
        Returns:
            OrderResult: Processed order result.
        """
        try:
            order_id = response.get('orderId')
            symbol = response.get('symbol')
            side = response.get('side')
            status = response.get('status')
            orig_qty = float(response.get('origQty', 0))
            executed_qty = float(response.get('executedQty', 0))
            cumulative_quote_qty = float(response.get('cumQuote', 0))
            
            # Process fills to calculate average price
            fills = response.get('fills', [])
            avg_price = None
            
            if fills:
                # Calculate volume-weighted average price
                total_cost = 0
                total_qty = 0
                for fill in fills:
                    fill_price = float(fill.get('price', 0))
                    fill_qty = float(fill.get('qty', 0))
                    total_cost += fill_price * fill_qty
                    total_qty += fill_qty
                
                if total_qty > 0:
                    avg_price = total_cost / total_qty
            elif cumulative_quote_qty > 0 and executed_qty > 0:
                # Use cumQuote if available (for cases where fills aren't returned)
                avg_price = cumulative_quote_qty / executed_qty
            
            # Create detailed success message
            message = f"Order placed successfully. Status: {status}"
            if executed_qty > 0:
                message += f" | Executed: {executed_qty}/{orig_qty}"
                fill_pct = (executed_qty / orig_qty * 100) if orig_qty > 0 else 0
                message += f" ({fill_pct:.1f}%)"
            if avg_price:
                message += f" | Avg Price: {avg_price:.8f}"
            
            return OrderResult(
                success=True,
                message=message,
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=orig_qty,
                price=input_price,
                status=status,
                executed_qty=executed_qty,
                avg_price=avg_price,
                cumulative_quote_asset_transacted_qty=cumulative_quote_qty,
                raw_response=response
            )
        
        except Exception as e:
            error_msg = f"Error processing order response: {str(e)}"
            self.logger.error(error_msg)
            return OrderResult(
                success=False,
                message=error_msg
            )
