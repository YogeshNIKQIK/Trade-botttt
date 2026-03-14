"""
Input validation for the trading bot CLI.
Validates symbol, side, order type, quantity, and price.
"""

from bot.logging_config import get_logger

logger = get_logger()


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol (e.g., BTCUSDT).

    Args:
        symbol: Trading pair symbol

    Returns:
        Uppercase symbol

    Raises:
        ValidationError: If symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol cannot be empty")
    s = symbol.strip().upper()
    if len(s) < 6:
        raise ValidationError(f"Invalid symbol '{symbol}': must be at least 6 characters (e.g., BTCUSDT)")
    if not s.endswith("USDT"):
        raise ValidationError(f"Invalid symbol '{symbol}': must end with USDT for USDT-M futures")
    return s


def validate_side(side: str) -> str:
    """
    Validate order side (BUY or SELL).

    Args:
        side: Order side

    Returns:
        Uppercase side

    Raises:
        ValidationError: If side is invalid
    """
    if not side or not isinstance(side, str):
        raise ValidationError("Side cannot be empty")
    s = side.strip().upper()
    if s not in ("BUY", "SELL"):
        raise ValidationError(f"Invalid side '{side}': must be BUY or SELL")
    return s


def validate_order_type(order_type: str) -> str:
    """
    Validate order type (MARKET, LIMIT, or STOP_LIMIT).

    Args:
        order_type: Order type

    Returns:
        Uppercase order type

    Raises:
        ValidationError: If order type is invalid
    """
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type cannot be empty")
    t = order_type.strip().upper()
    if t not in ("MARKET", "LIMIT", "STOP_LIMIT"):
        raise ValidationError(f"Invalid order type '{order_type}': must be MARKET, LIMIT, or STOP_LIMIT")
    return t


def validate_quantity(quantity: str | float) -> float:
    """
    Validate order quantity (positive number).

    Args:
        quantity: Order quantity

    Returns:
        Float quantity

    Raises:
        ValidationError: If quantity is invalid
    """
    try:
        q = float(quantity)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid quantity '{quantity}': must be a positive number") from e
    if q <= 0:
        raise ValidationError(f"Invalid quantity '{quantity}': must be greater than 0")
    return q


def validate_stop_price(stop_price: str | float, required: bool = False) -> float | None:
    """
    Validate stop price (trigger price for Stop-Limit orders).

    Args:
        stop_price: Trigger price
        required: Whether stop price is required

    Returns:
        Float stop price or None

    Raises:
        ValidationError: If stop price is invalid or missing when required
    """
    if stop_price is None or (isinstance(stop_price, str) and stop_price.strip() == ""):
        if required:
            raise ValidationError("Stop price is required for STOP_LIMIT orders")
        return None
    try:
        p = float(stop_price)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid stop price '{stop_price}': must be a positive number") from e
    if p <= 0:
        raise ValidationError(f"Invalid stop price '{stop_price}': must be greater than 0")
    return p


def validate_price(price: str | float, required: bool = False) -> float | None:
    """
    Validate price (positive number, required for LIMIT orders).

    Args:
        price: Order price (required for LIMIT)
        required: Whether price is required

    Returns:
        Float price or None if not required and not provided

    Raises:
        ValidationError: If price is invalid or missing when required
    """
    if price is None or (isinstance(price, str) and price.strip() == ""):
        if required:
            raise ValidationError("Price is required for LIMIT and STOP_LIMIT orders")
        return None
    try:
        p = float(price)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid price '{price}': must be a positive number") from e
    if p <= 0:
        raise ValidationError(f"Invalid price '{price}': must be greater than 0")
    return p


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict:
    """
    Validate all order parameters.

    Returns:
        Dict with validated values
    """
    validated = {}
    validated["symbol"] = validate_symbol(symbol)
    validated["side"] = validate_side(side)
    validated["order_type"] = validate_order_type(order_type)
    validated["quantity"] = validate_quantity(quantity)
    needs_price = validated["order_type"] in ("LIMIT", "STOP_LIMIT")
    needs_stop_price = validated["order_type"] == "STOP_LIMIT"
    validated["price"] = validate_price(price, required=needs_price)
    validated["stop_price"] = validate_stop_price(stop_price, required=needs_stop_price)
    return validated
