# Binance-Futures-Testnet-Trading-Bot

A modular Python-based trading bot for Binance Futures Testnet that supports Market Orders, Limit Orders, exchange rule validation, structured logging, retry mechanisms, and a command-line interface.

## Features

* Place Market Orders on Binance Futures Testnet
* Place Limit Orders on Binance Futures Testnet
* Symbol Validation
* Quantity Validation
* Price Validation
* Tick Size Validation
* Exchange Rule Validation
* Structured Logging
* Retry Mechanism with Exponential Backoff
* Environment-Based Configuration
* Interactive Command Line Interface
* Error Handling and User-Friendly Messages

## Project Structure

```
.
├── bot/
│   ├── __init__.py
│   ├── cli.py
│   ├── client.py
│   ├── config.py
│   ├── exceptions.py
│   ├── exchange_info.py
│   ├── logging_config.py
│   ├── orders.py
│   ├── retry.py
│   └── validators.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_integration.py
│   └── test_validators.py
│
├── requirements.txt
├── pytest.ini
├── setup.cfg
├── README.md
└── .gitignore
```

## Requirements

* Python 3.11+
* Binance Futures Testnet Account
* Binance Futures Testnet API Key and Secret

## Installation

### Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
BINANCE_API_KEY=YOUR_API_KEY
BINANCE_API_SECRET=YOUR_API_SECRET
```

Generate your API credentials from Binance Futures Testnet and paste them into the `.env` file.

## Running the Application

```bash
python -m bot.cli
```

## Main Menu

```
1. Place Market Order
2. Place Limit Order
3. View Recent Logs
4. Exit
```

## Example Market Order

```
Symbol: BTCUSDT
Side: BUY
Quantity: 0.001
```

Result:

```
ORDER SUCCESSFUL
Order ID: xxxxxxxxx
Status: NEW
```

## Example Limit Order

```
Symbol: BTCUSDT
Side: BUY
Quantity: 0.001
Price: 68008.8
```

Result:

```
ORDER SUCCESSFUL
Order ID: xxxxxxxxx
Status: NEW
```

## Validation Features

The application validates:

* Trading Symbol
* Order Side
* Quantity
* Price
* Tick Size
* Step Size
* Minimum and Maximum Price Limits
* Exchange Trading Rules

Example validation:

```
Price 68008.75 does not match tick size 0.1
Use increments of 0.1
```

## Logging

All trading activity and application events are logged.

Logged events include:

* Order Placement Attempts
* Successful Orders
* Validation Errors
* API Errors
* Connection Issues

## Testing

Run the test suite:

```bash
pytest
```

## Technologies Used

* Python
* Binance Futures API
* Requests
* Pytest
* Logging
* Environment Variables (.env)

## Architecture

```
CLI Layer
    ↓
Validation Layer
    ↓
Order Service Layer
    ↓
Binance Client Layer
    ↓
Binance Futures Testnet API
```

## Security

* API credentials are stored using environment variables.
* No API credentials are hardcoded.
* Sensitive configuration files are excluded using `.gitignore`.

## Known Limitation

Order placement works successfully on Binance Futures Testnet. In some cases, order status verification may return a signature validation error after successful order placement. This does not affect actual order execution.

## Future Improvements

* Stop Loss Orders
* Take Profit Orders
* Position Management
* Portfolio Tracking
* GUI Interface
* Automated Trading Strategies
* Database Integration
* Real-Time Notifications

## Author

Developed as part of an internship assignment demonstrating Binance Futures API integration, trading workflows, validation logic, logging, error handling, and modular software architecture.
