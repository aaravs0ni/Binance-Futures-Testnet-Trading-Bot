"""
Command-line interface module.
Entry point for the trading bot application.
Collects user inputs, validates them, and executes trading operations with menu-driven interface.
"""

import sys
import argparse
from typing import Optional, Tuple
from .config import get_config
from .client import BinanceClient
from .orders import OrderService, OrderResult
from .validators import InputValidator
from .exchange_info import ExchangeInfo
from .logging_config import setup_logging, get_logger
from . import exceptions


class TradingBotCLI:
    """Command-line interface for the trading bot."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.logger = None
        self.config = None
        self.client = None
        self.order_service = None
    
    def initialize(self) -> bool:
        """
        Initialize logging, configuration, and clients.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        """
        try:
            # Setup logging
            self.logger = setup_logging()
            self.logger.info("Trading Bot CLI starting...")
            
            # Load configuration
            self.config = get_config()
            self.logger.info("Configuration loaded successfully")
            
            # Initialize Binance client
            self.client = BinanceClient(
                api_key=self.config.get_api_key(),
                api_secret=self.config.get_api_secret(),
                base_url=self.config.get_testnet_base_url()
            )
            
            # Initialize order service
            self.order_service = OrderService(self.client)
            # Initialize exchange info and validator for rule checks
            try:
                self.exchange_info = ExchangeInfo(self.config.get_testnet_base_url())
            except Exception:
                self.exchange_info = None
            self.validator = InputValidator(self.exchange_info)
            
            return True
        
        except exceptions.ConfigurationError as e:
            print(f"\n❌ Configuration Error:\n   {str(e)}\n")
            if self.logger:
                self.logger.error(f"Configuration error: {str(e)}")
            return False
        
        except exceptions.AuthenticationError as e:
            print(f"\n❌ Authentication Error:\n   {str(e)}\n")
            if self.logger:
                self.logger.error(f"Authentication error: {str(e)}")
            return False
        
        except Exception as e:
            print(f"\n❌ Initialization Error:\n   {str(e)}\n")
            if self.logger:
                self.logger.error(f"Initialization error: {str(e)}")
            return False
    
    def display_menu(self) -> None:
        """Display the main menu."""
        print("\n" + "="*60)
        print("  BINANCE FUTURES TESTNET TRADING BOT")
        print("="*60)
        print("\nOptions:")
        print("  1. Place Market Order")
        print("  2. Place Limit Order")
        print("  3. View Recent Logs")
        print("  4. Exit")
        print("="*60)
    
    def get_menu_choice(self) -> str:
        """Get user's menu choice."""
        while True:
            choice = input("\nSelect an option (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def get_market_order_inputs(self) -> Optional[Tuple[str, str, str]]:
        """
        Get inputs for market order.
        
        Returns:
            Optional[Tuple[str, str, str]]: (symbol, side, quantity) or None if user cancels.
        """
        print("\n--- MARKET ORDER ---")
        
        symbol = input("Enter trading symbol (e.g., BTCUSDT): ").strip().upper()
        if not symbol:
            print("❌ Cancelled.")
            return None
        
        side = input("Enter order side (BUY/SELL): ").strip().upper()
        if not side:
            print("❌ Cancelled.")
            return None
        
        quantity = input("Enter quantity: ").strip()
        if not quantity:
            print("❌ Cancelled.")
            return None
        
        return symbol, side, quantity
    
    def get_limit_order_inputs(self) -> Optional[Tuple[str, str, str, str]]:
        """
        Get inputs for limit order.
        
        Returns:
            Optional[Tuple[str, str, str, str]]: (symbol, side, quantity, price) or None if user cancels.
        """
        print("\n--- LIMIT ORDER ---")
        
        symbol = input("Enter trading symbol (e.g., BTCUSDT): ").strip().upper()
        if not symbol:
            print("❌ Cancelled.")
            return None
        
        side = input("Enter order side (BUY/SELL): ").strip().upper()
        if not side:
            print("❌ Cancelled.")
            return None
        
        quantity = input("Enter quantity: ").strip()
        if not quantity:
            print("❌ Cancelled.")
            return None
        
        price = input("Enter price: ").strip()
        if not price:
            print("❌ Cancelled.")
            return None
        
        return symbol, side, quantity, price
    
    def display_order_summary(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None
    ) -> bool:
        """
        Display order summary and get user confirmation.
        
        Args:
            symbol (str): Trading symbol.
            side (str): Order side.
            order_type (str): Order type.
            quantity (str): Order quantity.
            price (Optional[str]): Order price.
        
        Returns:
            bool: True if user confirms, False otherwise.
        """
        print("\n" + "-"*50)
        print("ORDER SUMMARY")
        print("-"*50)
        print(f"Symbol:        {symbol}")
        print(f"Side:          {side}")
        print(f"Order Type:    {order_type}")
        print(f"Quantity:      {quantity}")
        if price:
            print(f"Price:         {price}")
        print("-"*50)
        
        confirm = input("\nProceed with this order? (yes/no): ").strip().lower()
        return confirm in ['yes', 'y']
    
    def display_order_result(self, result: OrderResult) -> None:
        """
        Display order result with details.
        
        Args:
            result (OrderResult): Order result to display.
        """
        if result.success:
            print("\n" + "="*50)
            print("✅ ORDER SUCCESSFUL")
            print("="*50)
            print(f"Message:       {result.message}")
            print(f"Order ID:      {result.order_id}")
            print(f"Status:        {result.status}")
            if result.executed_qty and result.executed_qty > 0:
                print(f"Executed Qty:  {result.executed_qty}")
            if result.avg_price and result.avg_price > 0:
                print(f"Avg Price:     {result.avg_price:.8f}")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("❌ ORDER FAILED")
            print("="*50)
            print(f"Error:         {result.message}")
            if result.symbol:
                print(f"Symbol:        {result.symbol}")
            if result.side:
                print(f"Side:          {result.side}")
            if result.quantity:
                print(f"Quantity:      {result.quantity}")
            print("="*50)
    
    def view_recent_logs(self) -> None:
        """Display recent log entries."""
        try:
            with open("logs/trading.log", "r") as log_file:
                lines = log_file.readlines()
                recent_lines = lines[-20:] if len(lines) > 20 else lines
            
            print("\n" + "="*60)
            print("RECENT LOG ENTRIES (Last 20)")
            print("="*60)
            for line in recent_lines:
                print(line.rstrip())
            print("="*60)
        
        except FileNotFoundError:
            print("\n❌ Log file not found.")
        except Exception as e:
            print(f"\n❌ Error reading logs: {str(e)}")
    
    def execute_market_order(self) -> None:
        """Execute market order workflow."""
        inputs = self.get_market_order_inputs()
        if not inputs:
            return
        
        symbol, side, quantity = inputs
        
        # Validate inputs
        try:
            self.validator.validate_all_inputs(symbol, side, "MARKET", quantity, "")
        except exceptions.ValidationError as e:
            print(f"\n❌ Validation Error: {str(e)}")
            self.logger.error(f"Market order validation error: {str(e)}")
            return
        
        # Display summary and get confirmation
        if not self.display_order_summary(symbol, side, "MARKET", quantity):
            print("❌ Order cancelled.")
            return
        
        # Execute order
        result = self.order_service.place_market_order(
            symbol=symbol,
            side=side,
            quantity=float(quantity)
        )
        
        # Display result
        self.display_order_result(result)
    
    def execute_limit_order(self) -> None:
        """Execute limit order workflow."""
        inputs = self.get_limit_order_inputs()
        if not inputs:
            return
        
        symbol, side, quantity, price = inputs
        
        # Validate inputs
        try:
            self.validator.validate_all_inputs(symbol, side, "LIMIT", quantity, price)
        except exceptions.ValidationError as e:
            print(f"\n❌ Validation Error: {str(e)}")
            self.logger.error(f"Limit order validation error: {str(e)}")
            return
        
        # Display summary and get confirmation
        if not self.display_order_summary(symbol, side, "LIMIT", quantity, price):
            print("❌ Order cancelled.")
            return
        
        # Execute order
        result = self.order_service.place_limit_order(
            symbol=symbol,
            side=side,
            quantity=float(quantity),
            price=float(price)
        )
        
        # Display result
        self.display_order_result(result)
    
    def run(self) -> None:
        """Run the main CLI loop."""
        # Initialize
        if not self.initialize():
            return
        
        print("\n✅ Connected to Binance Futures Testnet")
        
        # Main menu loop
        while True:
            self.display_menu()
            choice = self.get_menu_choice()
            
            if choice == '1':
                self.execute_market_order()
            elif choice == '2':
                self.execute_limit_order()
            elif choice == '3':
                self.view_recent_logs()
            elif choice == '4':
                print("\n👋 Goodbye!")
                self.logger.info("Trading Bot CLI closed")
                break


def main() -> None:
    """Main entry point for the application."""
    try:
        parser = argparse.ArgumentParser(description="Binance Futures Testnet Trading Bot CLI")
        parser.add_argument('--symbol', type=str, help='Trading symbol (e.g., BTCUSDT)')
        parser.add_argument('--side', type=str, choices=['BUY', 'SELL'], help='Order side')
        parser.add_argument('--type', dest='order_type', type=str, choices=['MARKET', 'LIMIT'], help='Order type')
        parser.add_argument('--quantity', type=str, help='Order quantity')
        parser.add_argument('--price', type=str, help='Limit order price')
        parser.add_argument('--yes', action='store_true', help='Auto-confirm the order (non-interactive)')

        args = parser.parse_args()

        cli = TradingBotCLI()

        # If symbol provided, run non-interactive single-order mode
        if args.symbol:
            if not cli.initialize():
                sys.exit(1)

            # Ensure required args present
            if not args.side or not args.order_type or not args.quantity:
                print("\n❌ For non-interactive mode, --symbol, --side, --type, and --quantity are required")
                sys.exit(2)

            symbol = args.symbol.strip().upper()
            side = args.side.strip().upper()
            order_type = args.order_type.strip().upper()
            quantity = args.quantity.strip()
            price = args.price.strip() if args.price else ""

            # Validate inputs
            try:
                cli.validator.validate_all_inputs(symbol, side, order_type, quantity, price)
            except exceptions.ValidationError as e:
                print(f"\n❌ Validation Error: {str(e)}")
                sys.exit(3)

            # Require explicit confirmation in non-interactive mode unless --yes
            if not args.yes:
                print("\n❌ Non-interactive mode requires --yes to auto-confirm orders")
                sys.exit(4)

            # Execute order
            if order_type == 'MARKET':
                result = cli.order_service.place_market_order(symbol, side, float(quantity))
            else:
                if not price:
                    print("\n❌ Limit orders require --price")
                    sys.exit(5)
                result = cli.order_service.place_limit_order(symbol, side, float(quantity), float(price))

            cli.display_order_result(result)
            return

        # Otherwise run interactive menu
        cli.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
