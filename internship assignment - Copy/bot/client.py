"""
Binance client module.
Manages all communication with Binance Futures Testnet.
Handles API initialization, retries, session management, and provides reusable methods for exchange interaction.
"""

from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as UrllibRetry
from urllib.parse import urlencode
import hmac
import hashlib
import time
import uuid
import json
from . import exceptions
from .logging_config import get_logger
from .retry import retry_with_backoff, RetryConfig, is_retryable, classify_api_error


class BinanceClient:
    """
    Binance Futures Testnet client with resilience features.
    
    Features:
    - Session reuse and connection pooling
    - Retry mechanism with exponential backoff
    - Comprehensive request/response logging
    - Response schema validation
    - API permission verification
    - Transient vs permanent error classification
    """
    
    # Required API permissions for this application
    REQUIRED_PERMISSIONS = ['Futures', 'Enable Reading', 'Enable Spot and Margin Trading']
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        verify_permissions: bool = True,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize Binance client with API credentials and session management.
        
        Args:
            api_key (str): Binance API key.
            api_secret (str): Binance API secret.
            base_url (str): Binance Futures Testnet base URL.
            verify_permissions (bool): Verify API key permissions on startup.
            retry_config (Optional[RetryConfig]): Retry configuration.
        
        Raises:
            AuthenticationError: If API credentials are invalid.
            ConnectionError: If connection fails.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.logger = get_logger()
        
        # Retry configuration
        self.retry_config = retry_config or RetryConfig()
        
        # Create persistent session with connection pooling
        self.session = self._create_session()
        
        # Test authentication with lightweight ping endpoint (permissionless)
        self._test_connection()
        
        # Verify API permissions
        if verify_permissions:
            self._verify_api_permissions()
    
    def _create_session(self) -> requests.Session:
        """
        Create a persistent HTTP session with connection pooling and retry logic.
        
        Returns:
            requests.Session: Configured session with pooling.
        """
        session = requests.Session()
        
        # Configure connection pooling
        # Keep connections alive to reuse them
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=UrllibRetry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=['GET', 'POST', 'DELETE']
            )
        )
        
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        
        return session
    
    def _test_connection(self) -> None:
        """
        Test the connection to Binance using a lightweight permissionless endpoint.
        
        Raises:
            AuthenticationError: If connection fails.
            ConnectionError: If network issues occur.
        """
        try:
            # Use server time endpoint (no authentication needed) to verify connectivity
            response = self.session.get(
                f"{self.base_url}/fapi/v1/time",
                timeout=10
            )
            response.raise_for_status()
            self.logger.info("Binance Futures Testnet reachable (server time OK)")

            # Optionally fetch exchangeInfo (permissionless) to prime symbol cache
            try:
                ex_resp = self.session.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
                if ex_resp.status_code == 200:
                    self.logger.debug("Fetched exchangeInfo during startup")
            except Exception:
                # Non-fatal: exchangeInfo fetching failure shouldn't block startup
                self.logger.debug("Could not fetch exchangeInfo at startup; continuing")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Connection failed: {str(e)}")
            raise exceptions.ConnectionError(f"Failed to reach Binance: {str(e)}")
    
    def _verify_api_permissions(self) -> None:
        """
        Verify that API key has required permissions for trading.
        
        Raises:
            AuthenticationError: If permissions are insufficient.
        """
        try:
            account = self._make_request("GET", "/fapi/v2/account")
            
            # Check if account is valid
            if not account.get('canTrade'):
                raise exceptions.AuthenticationError(
                    "API key does not have trading permissions enabled"
                )
            
            if not account.get('canDeposit') and not account.get('canWithdraw'):
                self.logger.warning(
                    "API key does not have deposit/withdraw permissions. "
                    "This may limit functionality but trading should work."
                )
            
            self.logger.info("API permissions verified")
        
        except exceptions.AuthenticationError:
            raise
        except Exception as e:
            self.logger.warning(f"Could not verify API permissions: {str(e)}")
    
    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC SHA256 signature for request authentication.
        
        Args:
            query_string (str): Query string to sign.
        
        Returns:
            str: Signature hash.
        """
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID for logging correlation.
        
        Returns:
            str: UUID request ID.
        """
        return str(uuid.uuid4())
    
    def _validate_response_schema(
        self,
        response_data: Dict[str, Any],
        expected_fields: Optional[list] = None
    ) -> bool:
        """
        Validate that API response contains expected fields.
        
        Args:
            response_data (Dict): Response JSON.
            expected_fields (Optional[list]): Expected fields in response.
        
        Returns:
            bool: True if response is valid, False otherwise.
        """
        if expected_fields is None:
            return True  # No validation needed
        
        for field in expected_fields:
            if field not in response_data:
                self.logger.warning(
                    f"Response missing expected field: {field}. "
                    f"Response: {response_data}"
                )
                return False
        
        return True
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        expected_fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Binance API with retry logic.
        
        Args:
            method (str): HTTP method (GET, POST, DELETE, etc.).
            endpoint (str): API endpoint path.
            params (Optional[Dict]): Query parameters.
            data (Optional[Dict]): Request body data.
            expected_fields (Optional[list]): Expected fields in response.
        
        Returns:
            Dict[str, Any]: Response JSON data.
        
        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If network issues occur.
            RateLimitError: If rate limit is exceeded.
            OrderPlacementError: For other API errors.
        """
        request_id = self._generate_request_id()
        
        def _attempt_request():
            try:
                url = f"{self.base_url}{endpoint}"
               # print("BASE URL:", self.base_url)4
               # print("FULL URL:", url)
               # print("METHOD:", method)
                headers = {
                    "X-MBX-APIKEY": self.api_key,
                    "X-Request-ID": request_id
                }
                
                # Prepare parameters with timestamp
                if params is None:
                    request_params = {}
                else:
                    request_params = params.copy()
                
                request_params['timestamp'] = int(time.time() * 1000)
                
                # Normalize all values to strings before signing
                normalized_params = {k: str(v) for k, v in request_params.items()}
                sorted_params = sorted(normalized_params.items())
                query_string = urlencode(sorted_params, doseq=True)
                signature = self._generate_signature(query_string)
                # print("QUERY STRING:", query_string)
               # print("SIGNATURE:", signature)

                # Log request details
                self.logger.debug(
                    f"[{request_id}] {method} {endpoint} - params={query_string}"
                )
                
                # Choose transport mode based on HTTP method
                request_kwargs = {
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'timeout': 10
                }
                if method.upper() == 'POST':
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    request_body = f"{query_string}&signature={signature}"
                    request_kwargs['data'] = request_body
                    self.logger.debug(f"[{request_id}] Request body: {request_body}")
                else:
                    normalized_params['signature'] = signature
                    request_kwargs['params'] = normalized_params
                
                # Make request with session
                response = self.session.request(**request_kwargs)
                self.logger.debug(
                    f"[{request_id}] Sent URL: {response.request.url}"
                )
                if response.request.body:
                    self.logger.debug(
                        f"[{request_id}] Sent BODY: {response.request.body}"
                    )
                
                # Log full response
                response_body = response.text[:500] if response.text else ""
                self.logger.debug(
                    f"[{request_id}] Response {response.status_code}: {response_body}"
                )
                
                # Handle different status codes
                if response.status_code == 401:
                    self.logger.error(f"[{request_id}] Unauthorized: Invalid API credentials")
                    raise exceptions.AuthenticationError("Invalid API credentials")
                
                if response.status_code == 403:
                    self.logger.error(f"[{request_id}] Forbidden: Access denied")
                    raise exceptions.AuthenticationError("Access denied")
                
                if response.status_code == 429:
                    self.logger.warning(f"[{request_id}] Rate limit exceeded")
                    raise exceptions.RateLimitError("API rate limit exceeded. Please try again later.")
                
                if response.status_code >= 500:
                    self.logger.warning(
                        f"[{request_id}] Server error: {response.status_code}"
                    )
                    raise exceptions.ConnectionError(
                        f"Binance server error: {response.status_code}"
                    )
                
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('msg', response.text)
                    except:
                        error_msg = response.text
                    
                    self.logger.error(
                        f"[{request_id}] API error {response.status_code}: {error_msg}"
                    )
                    raise exceptions.OrderPlacementError(f"API error: {error_msg}")
                
                # Parse response
                try:
                    response_json = response.json()
                except:
                    self.logger.error(f"[{request_id}] Invalid JSON response: {response.text}")
                    raise exceptions.ConnectionError("Invalid API response format")
                
                # Validate response schema
                if expected_fields and not self._validate_response_schema(
                    response_json,
                    expected_fields
                ):
                    self.logger.warning(
                        f"[{request_id}] Response missing expected fields"
                    )
                
                return response_json
            
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"[{request_id}] Connection error: {str(e)}")
                raise exceptions.ConnectionError(f"Failed to connect to Binance: {str(e)}")
            
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"[{request_id}] Request timeout: {str(e)}")
                raise exceptions.ConnectionError(f"Request timeout: {str(e)}")
            
            except exceptions.TradingBotException:
                raise
            
            except Exception as e:
                self.logger.error(f"[{request_id}] Unexpected error: {str(e)}")
                raise exceptions.TradingBotException(f"Unexpected error: {str(e)}")
        
        # Execute with retry logic
        return retry_with_backoff(
            _attempt_request,
            config=self.retry_config,
            logger=self.logger
        )

    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Dict[str, Any]:
        """
        Place a market order on Binance Futures.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT').
            side (str): Order side ('BUY' or 'SELL').
            quantity (float): Order quantity.
        
        Returns:
            Dict[str, Any]: Order response from Binance Futures.
        
        Raises:
            OrderPlacementError: If order placement fails.
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity
        }
        
        self.logger.info(
            f"Placing MARKET order: {side} {quantity} {symbol}"
        )
        
        # Expected fields in Futures response
        expected_fields = ['orderId', 'symbol', 'status', 'executedQty']
        
        return self._make_request(
            "POST",
            "/fapi/v1/order",
            params=params,
            expected_fields=expected_fields
        )
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Place a limit order on Binance Futures.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT').
            side (str): Order side ('BUY' or 'SELL').
            quantity (float): Order quantity.
            price (float): Order price.
            time_in_force (str): Time in force ('GTC', 'IOC', 'FOK'). Defaults to 'GTC'.
        
        Returns:
            Dict[str, Any]: Order response from Binance Futures.
        
        Raises:
            OrderPlacementError: If order placement fails.
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'timeInForce': time_in_force,
            'quantity': quantity,
            'price': price
        }
        
        self.logger.info(
            f"Placing LIMIT order: {side} {quantity} {symbol} @ {price}"
        )
        
        # Expected fields in Futures response
        expected_fields = ['orderId', 'symbol', 'status', 'executedQty']
        
        return self._make_request(
            "POST",
            "/fapi/v1/order",
            params=params,
            expected_fields=expected_fields
        )
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balances and trading permissions.
        
        Returns:
            Dict[str, Any]: Account information.
        
        Raises:
            ConnectionError: If the request fails.
        """
        expected_fields = ['canTrade', 'canDeposit', 'canWithdraw']
        return self._make_request(
            "GET",
            "/fapi/v2/account",
            expected_fields=expected_fields
        )
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol (str): Trading symbol.
            order_id (int): Order ID to cancel.
        
        Returns:
            Dict[str, Any]: Cancellation response.
        """
        params = {'symbol': symbol, 'orderId': order_id}
        return self._make_request("DELETE", "/fapi/v1/order", params=params)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get the current status of an existing order.
        
        Args:
            symbol (str): Trading symbol.
            order_id (int): Order ID to query.
        
        Returns:
            Dict[str, Any]: Order status information including fills.
        """
        params = {'symbol': symbol, 'orderId': order_id}
        expected_fields = ['orderId', 'status', 'executedQty']
        return self._make_request(
            "GET",
            "/fapi/v1/order",
            params=params,
            expected_fields=expected_fields
        )
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all open orders for a symbol or across all symbols.
        
        Args:
            symbol (Optional[str]): Trading symbol. If None, returns all open orders.
        
        Returns:
            list: List of open orders.
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request("GET", "/fapi/v1/openOrders", params=params)
    
    def get_all_orders(self, symbol: str, limit: int = 500) -> list:
        """
        Get historical orders for a symbol.
        
        Args:
            symbol (str): Trading symbol.
            limit (int): Maximum number of orders to return.
        
        Returns:
            list: List of historical orders.
        """
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request("GET", "/fapi/v1/allOrders", params=params)
    
    def get_position_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get position information for account.
        
        Args:
            symbol (Optional[str]): Trading symbol. If None, returns all positions.
        
        Returns:
            Dict[str, Any]: Position information.
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request("GET", "/fapi/v2/account", params=params)
    
    def get_leverage(self, symbol: str) -> int:
        """
        Get current leverage for a symbol.
        
        Args:
            symbol (str): Trading symbol.
        
        Returns:
            int: Current leverage setting.
        """
        # This would typically be in account info
        account = self.get_account_info()
        for position in account.get('positions', []):
            if position.get('symbol') == symbol:
                return position.get('leverage', 1)
        return 1
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set leverage for a symbol.
        
        Args:
            symbol (str): Trading symbol.
            leverage (int): Desired leverage (typically 1-125).
        
        Returns:
            Dict[str, Any]: Response from Binance.
        """
        params = {'symbol': symbol, 'leverage': leverage}
        self.logger.info(f"Setting leverage for {symbol} to {leverage}x")
        return self._make_request("POST", "/fapi/v1/leverage", params=params)
    
    def get_position_mode(self) -> Dict[str, Any]:
        """
        Get position mode (One-way or Hedge mode).
        
        Returns:
            Dict[str, Any]: Position mode information.
        """
        return self._make_request("GET", "/fapi/v1/positionSide/dual")
    
    def set_position_mode(self, dual_side_position: bool) -> Dict[str, Any]:
        """
        Set position mode (One-way or Hedge mode).
        
        Args:
            dual_side_position (bool): True for Hedge mode, False for One-way mode.
        
        Returns:
            Dict[str, Any]: Response from Binance.
        """
        params = {'dualSidePosition': str(dual_side_position).lower()}
        mode = "Hedge" if dual_side_position else "One-way"
        self.logger.info(f"Setting position mode to: {mode}")
        return self._make_request("POST", "/fapi/v1/positionSide/dual", params=params)
