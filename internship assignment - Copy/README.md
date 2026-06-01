# Binance Futures Testnet Trading Bot

A production-ready, modular Python application for placing trading orders on Binance Futures Testnet (USDT-M Futures). Built with clean architecture, comprehensive error handling, structured logging, and a user-friendly command-line interface.

## Features

- **Menu-Driven Interface**: Interactive CLI with options to place market orders, place limit orders, view logs, or exit
- **Market Orders**: Quick execution at current market price
- **Limit Orders**: Place orders at specified prices
- **Input Validation**: Comprehensive validation of all user inputs with meaningful error messages
- **Secure Configuration**: API credentials loaded from `.env` file, never hardcoded
- **Structured Logging**: All trading attempts, API responses, and errors logged to `logs/trading.log`
- **Error Handling**: Graceful handling of validation errors, API failures, network issues, and rate limits
- **Modular Architecture**: Clean separation of concerns across dedicated modules
- **Order Results**: Detailed feedback including order ID, status, execution details, and average price

## Project Structure

```
project_root/
├── bot/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── client.py                # Binance API client
│   ├── validators.py            # Input validation
│   ├── exceptions.py            # Custom exception classes
│   ├── logging_config.py        # Logging configuration
│   ├── orders.py                # Trading business logic
│   ├── cli.py                   # Command-line interface
│   └── logs/                    # Directory for log files
│       └── trading.log          # Application logs
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (not in version control)
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Installation

### 1. Clone or Download the Project

```bash
cd path/to/project
```

### 2. Create a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Credentials

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com)
2. Sign up or log in to your account
3. Go to **Account** → **API Management**
4. Create a new API key
5. Copy your API Key and Secret Key
6. Edit the `.env` file in the project root:

```env
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_api_secret_here
```

⚠️ **Never commit the `.env` file to version control. It's already in `.gitignore`.**

## Usage

### Running the Application

**On Windows (PowerShell):**
```powershell
python -m bot.cli
```

**On Windows (Command Prompt):**
```cmd
python -m bot.cli
```

**On macOS/Linux:**
```bash
python -m bot.cli
```

### Using the Menu Interface

Once the application starts, you'll see the main menu:

```
==============================================================
  BINANCE FUTURES TESTNET TRADING BOT
==============================================================

Options:
  1. Place Market Order
  2. Place Limit Order
  3. View Recent Logs
  4. Exit
==============================================================
```

#### Example 1: Placing a Market Order

```
Select an option (1-4): 1

--- MARKET ORDER ---
Enter trading symbol (e.g., BTCUSDT): BTCUSDT
Enter order side (BUY/SELL): BUY
Enter quantity: 0.001

--------------------------------------------------
ORDER SUMMARY
--------------------------------------------------
Symbol:        BTCUSDT
Side:          BUY
Order Type:    MARKET
Quantity:      0.001
--------------------------------------------------

Proceed with this order? (yes/no): yes

==================================================
✅ ORDER SUCCESSFUL
==================================================
Message:       Order placed successfully. Status: FILLED
Order ID:      12345678
Status:        FILLED
Executed Qty:  0.001
Avg Price:     45000.50000000
==================================================
```

#### Example 2: Placing a Limit Order

```
Select an option (1-4): 2

--- LIMIT ORDER ---
Enter trading symbol (e.g., BTCUSDT): ETHUSDT
Enter order side (BUY/SELL): BUY
Enter quantity: 0.5
Enter price: 2500.50

--------------------------------------------------
ORDER SUMMARY
--------------------------------------------------
Symbol:        ETHUSDT
Side:          BUY
Order Type:    LIMIT
Quantity:      0.5
Price:         2500.50
--------------------------------------------------

Proceed with this order? (yes/no): yes

==================================================
✅ ORDER SUCCESSFUL
==================================================
Message:       Order placed successfully. Status: NEW
Order ID:      12345679
Status:        NEW
==================================================
```

#### Example 3: Viewing Recent Logs

```
Select an option (1-4): 3

============================================================
RECENT LOG ENTRIES (Last 20)
============================================================
2024-01-15 10:30:45 - TradingBot - INFO - Trading Bot CLI starting...
2024-01-15 10:30:45 - TradingBot - INFO - Configuration loaded successfully
2024-01-15 10:30:46 - TradingBot - INFO - Successfully authenticated with Binance Futures Testnet
2024-01-15 10:31:02 - TradingBot - INFO - Market order initiated: BUY 0.001 BTCUSDT
2024-01-15 10:31:03 - TradingBot - INFO - Placing MARKET order: BUY 0.001 BTCUSDT
2024-01-15 10:31:04 - TradingBot - INFO - Market order successful: Order placed successfully...
============================================================
```

## Module Details

### `config.py`
- Loads environment variables from `.env` file
- Validates that all required settings (API key, secret) are available
- Provides centralized access to configuration throughout the application
- Raises `ConfigurationError` if required settings are missing

### `client.py`
- Manages all communication with Binance Futures Testnet API
- Handles API authentication with HMAC SHA256 signatures
- Provides methods: `place_market_order()`, `place_limit_order()`, `get_account_info()`, etc.
- Handles different HTTP status codes and raises appropriate exceptions
- No business logic—only exchange communication

### `validators.py`
- Validates trading symbol (must be uppercase, alphanumeric, end with USDT)
- Validates order side (BUY or SELL)
- Validates order type (MARKET or LIMIT)
- Validates quantity (positive number)
- Validates price (positive number, required for limit orders)
- Provides meaningful error messages for each validation failure

### `exceptions.py`
- Defines custom exception hierarchy for different failure scenarios
- Base exception: `TradingBotException`
- Specific exceptions: `ConfigurationError`, `ValidationError`, `AuthenticationError`, `ConnectionError`, `OrderPlacementError`, `RateLimitError`, and others
- Enables clean error handling and informative user feedback

### `logging_config.py`
- Configures application-wide logging to `logs/trading.log`
- Logs include timestamp, logger name, log level, and message
- File handler logs all events; console handler shows only warnings and errors
- Logs: order requests, API responses, validation failures, authentication errors, and exceptions

### `orders.py`
- Contains trading business logic
- `OrderService` class manages order placement
- `OrderResult` class provides structured results with consistency
- Separate workflows for market and limit orders
- Processes Binance API responses and extracts relevant information
- Logs all trading attempts and results

### `cli.py`
- Entry point for the application
- Menu-driven interface with options for different operations
- Collects user inputs interactively
- Displays order summaries before execution for confirmation
- Presents clear success or failure messages
- Integrates all other modules for end-to-end workflow

## Input Validation Rules

### Symbol
- Cannot be empty
- Minimum 3 characters
- Must be uppercase, alphanumeric, and end with 'USDT'
- Examples: `BTCUSDT`, `ETHUSDT`, `BNBUSDT`

### Side
- Must be `BUY` or `SELL` (case-insensitive)

### Order Type
- Must be `MARKET` or `LIMIT` (case-insensitive)

### Quantity
- Must be a valid positive number
- Cannot be zero or negative

### Price (Limit Orders Only)
- Required for limit orders
- Must be a valid positive number
- Not required for market orders

## Error Handling

The application handles various failure scenarios gracefully:

| Error Type | Cause | User Message | Log Entry |
|------------|-------|--------------|-----------|
| Validation Error | Invalid input format | Descriptive error message | Error logged with details |
| Configuration Error | Missing API credentials | Configuration error details | Error logged with missing settings |
| Authentication Error | Invalid/expired API keys | Authentication failed message | Error logged |
| Connection Error | Network issues or server down | Connection error message | Error logged with details |
| Rate Limit Error | Too many API requests | Rate limit exceeded message | Error logged |
| Order Placement Error | Binance rejects order | Binance error message | Error logged |

## Logging

All application events are logged to `logs/trading.log`:

```
2024-01-15 10:30:45 - TradingBot - INFO - Trading Bot CLI starting...
2024-01-15 10:30:45 - TradingBot - INFO - Configuration loaded successfully
2024-01-15 10:30:46 - TradingBot - INFO - Successfully authenticated with Binance Futures Testnet
2024-01-15 10:31:02 - TradingBot - INFO - Market order initiated: BUY 0.001 BTCUSDT
2024-01-15 10:31:03 - TradingBot - INFO - Placing MARKET order: BUY 0.001 BTCUSDT
2024-01-15 10:31:04 - TradingBot - INFO - Market order successful: Order placed successfully. Status: FILLED (Order ID: 12345678)
```

Log entries include:
- Timestamp
- Logger name
- Log level (INFO, WARNING, ERROR, etc.)
- Descriptive message
- For errors: error type, message, and context

View recent logs using the CLI menu option or check the file directly:

```bash
cat logs/trading.log           # macOS/Linux
type logs\trading.log          # Windows Command Prompt
Get-Content logs\trading.log   # Windows PowerShell
```

## Assumptions

1. **Testnet Usage**: Application is designed for Binance Futures Testnet (not live trading)
2. **USDT-M Futures**: Only USDT-Margined Futures trading is supported
3. **Internet Connection**: Requires active internet connection to reach Binance API
4. **Python Version**: Requires Python 3.6+
5. **API Rate Limits**: Binance Futures API has rate limits; the application will raise an error if exceeded
6. **Order Execution**: Market orders execute immediately; limit orders may not execute if price is not reached
7. **Precision**: Asset quantities and prices follow Binance's precision requirements

## Troubleshooting

### "Configuration validation failed: BINANCE_API_KEY is not set"

**Solution**: Make sure you've created and configured the `.env` file with your API credentials.

```bash
# Create .env file (if it doesn't exist)
# Add your credentials
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

### "Invalid API credentials" / "Unauthorized"

**Solutions**:
1. Verify your API Key and Secret are correctly copied from Binance
2. Ensure there are no extra spaces in the `.env` file
3. Regenerate your API key on the Binance Testnet website
4. Verify the API key is active

### "Failed to connect to Binance"

**Solutions**:
1. Check your internet connection
2. Verify Binance Futures Testnet is operational
3. Check if your firewall is blocking the connection
4. Try again after a few moments

### "Symbol must follow Binance naming conventions"

**Solution**: Use valid Binance Futures symbols:
- Must end with `USDT`
- Examples: `BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `ADAUSDT`

### "Rate limit exceeded"

**Solution**: Wait a few minutes before trying again. Binance API has request rate limits.

### "Quantity must be a positive number"

**Solution**: Enter a valid positive number for the quantity (e.g., `0.001`, `1`, `10.5`)

### "Price is required for limit orders"

**Solution**: When placing a limit order, you must specify a price at which you want the order to execute.

## Future Enhancements

Possible extensions to this project:

1. **Additional Order Types**: GTC, IOC, FOK time-in-force options; Stop-Loss and Take-Profit orders
2. **Order Management**: View open orders, cancel orders, modify orders
3. **Trading Strategies**: Automated trading strategies, backtesting
4. **Multiple Exchanges**: Support for additional exchanges (Kraken, Coinbase, etc.)
5. **GUI Interface**: Graphical user interface using PyQt or Tkinter
6. **Database Integration**: Store order history in a database
7. **Notifications**: Email or SMS alerts for order execution
8. **Advanced Analytics**: Portfolio tracking, performance analysis

## Security Notes

- **API Credentials**: Never share your API keys or secret keys
- **Testnet Only**: This bot is configured for testnet trading (not live)
- **.env File**: Keep `.env` file local and never commit to version control
- **API Key Permissions**: On Binance, restrict API key permissions to futures trading only
- **IP Whitelist**: Consider whitelisting your IP address on Binance for extra security

## Development

### Project Architecture

The application follows a **layered architecture**:

```
┌─────────────────────┐
│   CLI Layer         │ (cli.py)
│   User Interface    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Validation Layer    │ (validators.py)
│ Input Validation    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Service Layer       │ (orders.py)
│ Business Logic      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Client Layer        │ (client.py)
│ API Communication   │
└─────────────────────┘
```

### Module Responsibilities

- **CLI** (`cli.py`): User interaction only
- **Validators** (`validators.py`): Input validation
- **Orders** (`orders.py`): Trading business logic
- **Client** (`client.py`): Exchange API communication
- **Config** (`config.py`): Configuration management
- **Exceptions** (`exceptions.py`): Error definitions
- **Logging** (`logging_config.py`): Application logging

### Testing

To test the application:

1. Start the application
2. Use the testnet environment (no real money at risk)
3. Try different order types and symbols
4. Check logs for all operations
5. Test error scenarios (invalid inputs, etc.)

## License

This project is provided as-is for educational and trading purposes.

## Support

For issues or questions:

1. Check the Troubleshooting section
2. Review the logs in `logs/trading.log`
3. Verify your configuration in `.env`
4. Check Binance Futures Testnet documentation

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Status**: Production-Ready
