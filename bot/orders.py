"""
Order placement logic for the trading bot.
Coordinates validation, client calls, and response formatting.
"""

from bot.client import BinanceClient, BinanceClientError
from bot.validators import ValidationError, validate_all
from bot.logging_config import get_logger

logger = get_logger()


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict:
    """
    Validate inputs, place order via client, and return formatted response.

    Args:
        client: Binance API client instance
        symbol: Trading pair (e.g., BTCUSDT)
        side: BUY or SELL
        order_type: MARKET, LIMIT, or STOP_LIMIT
        quantity: Order quantity
        price: Limit price (required for LIMIT and STOP_LIMIT)
        stop_price: Trigger price (required for STOP_LIMIT)

    Returns:
        Dict with order response details (orderId, status, executedQty, avgPrice, etc.)

    Raises:
        ValidationError: On invalid input
        BinanceClientError: On API or network error
    """
    validated = validate_all(
        symbol=symbol, side=side, order_type=order_type,
        quantity=quantity, price=price, stop_price=stop_price,
    )

    logger.info(
        "Placing order: symbol=%s side=%s type=%s quantity=%s price=%s stop_price=%s",
        validated["symbol"],
        validated["side"],
        validated["order_type"],
        validated["quantity"],
        validated["price"],
        validated.get("stop_price"),
    )

    response = client.place_order(
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["order_type"],
        quantity=validated["quantity"],
        price=validated["price"],
        stop_price=validated.get("stop_price"),
    )

    return response


def format_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: float | None = None,
    stop_price: float | None = None,
) -> str:
    """Format a human-readable order request summary."""
    lines = [
        "--- Order Request Summary ---",
        f"  Symbol:     {symbol}",
        f"  Side:       {side}",
        f"  Type:       {order_type}",
        f"  Quantity:   {quantity}",
    ]
    if price is not None:
        lines.append(f"  Price:      {price}")
    if stop_price is not None:
        lines.append(f"  Stop Price: {stop_price}")
    lines.append("--------------------------")
    return "\n".join(lines)


def format_order_response(response: dict, is_algo: bool = False) -> str:
    """Format order response for display. Algo orders (STOP_LIMIT) have different fields."""
    if is_algo:
        order_id = response.get("algoId", "N/A")
        status = response.get("algoStatus", "N/A")
        trigger_price = response.get("triggerPrice", "N/A")
        price = response.get("price", "N/A")
        return "\n".join([
            "--- Order Response (Algo) ---",
            f"  Algo ID:      {order_id}",
            f"  Status:       {status}",
            f"  Trigger:      {trigger_price}",
            f"  Limit Price:  {price}",
            "----------------------------",
        ])

    order_id = response.get("orderId", "N/A")
    status = response.get("status", "N/A")
    executed_qty = response.get("executedQty", response.get("origQty", "N/A"))
    avg_price = response.get("avgPrice")
    if avg_price is not None and str(avg_price) != "0":
        avg_price_str = str(avg_price)
    else:
        avg_price_str = "N/A (may fill later for LIMIT)"
    stop_price = response.get("stopPrice")

    lines = [
        "--- Order Response ---",
        f"  Order ID:    {order_id}",
        f"  Status:      {status}",
        f"  Executed:    {executed_qty}",
        f"  Avg Price:   {avg_price_str}",
    ]
    if stop_price is not None:
        lines.append(f"  Stop Price:  {stop_price}")
    lines.append("----------------------")
    return "\n".join(lines)
