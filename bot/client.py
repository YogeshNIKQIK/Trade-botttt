"""
Binance Futures Testnet API client wrapper.
Handles authenticated REST requests to the Binance Futures API.
"""

import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import requests

from bot.logging_config import get_logger

logger = get_logger()

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error."""

    pass


class BinanceClient:
    """
    Binance Futures Testnet API client.
    Uses direct REST calls with HMAC SHA256 signature authentication.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        """
        Initialize the Binance API client.

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            base_url: API base URL (default: testnet)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

    def _sign(self, params: dict) -> str:
        """Generate HMAC SHA256 signature for the query string."""
        query = urllib.parse.urlencode(params, safe="")
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to the Binance API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /fapi/v1/order)
            params: Query/body parameters
            signed: Whether to add signature (for authenticated endpoints)

        Returns:
            JSON response as dict

        Raises:
            BinanceClientError: On API error or network failure
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)

        if signed:
            params["signature"] = self._sign(params)

        headers = {"X-MBX-APIKEY": self.api_key}

        logger.info("API Request: %s %s | params: %s", method, endpoint, {
            k: v if k not in ("signature",) else "***" for k, v in params.items()
        })

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=30)
            else:
                response = requests.post(url, params=params, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error("Network error: %s", str(e))
            raise BinanceClientError(f"Network error: {e}") from e

        logger.info("API Response: status=%d body=%s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError as e:
            logger.error("Invalid JSON response: %s", response.text)
            raise BinanceClientError(f"Invalid API response: {response.text}") from e

        if not response.ok:
            code = data.get("code", -1)
            msg = data.get("msg", response.text)
            logger.error("API error: code=%s msg=%s", code, msg)
            if code == -2021 and "immediately trigger" in str(msg).lower():
                msg = f"{msg} (BUY: trigger must be above current price; SELL: trigger must be below current price)"
            raise BinanceClientError(f"API error [{code}]: {msg}")

        return data

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        """
        Place an order on Binance Futures.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            order_type: MARKET, LIMIT, or STOP_LIMIT
            quantity: Order quantity
            price: Limit price (required for LIMIT and STOP_LIMIT)
            stop_price: Trigger price (required for STOP_LIMIT)
            time_in_force: GTC, IOC, or FOK (for LIMIT and STOP_LIMIT)

        Returns:
            Order response from API
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise BinanceClientError("Price is required for LIMIT orders")
            params["price"] = price
            params["timeInForce"] = time_in_force
            return self._request("POST", "/fapi/v1/order", params=params)
        elif order_type == "STOP_LIMIT":
            if price is None:
                raise BinanceClientError("Price is required for STOP_LIMIT orders")
            if stop_price is None:
                raise BinanceClientError("Stop price is required for STOP_LIMIT orders")
            # Binance Futures uses Algo Order API for stop-limit (error -4120 on /fapi/v1/order)
            algo_params = {
                "algoType": "CONDITIONAL",
                "symbol": symbol,
                "side": side,
                "type": "STOP",
                "quantity": quantity,
                "price": price,
                "triggerPrice": stop_price,
                "timeInForce": time_in_force,
            }
            return self._request("POST", "/fapi/v1/algoOrder", params=algo_params)

        # MARKET orders
        return self._request("POST", "/fapi/v1/order", params=params)
