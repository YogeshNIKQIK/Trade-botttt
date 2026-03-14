"""
CLI entry point for the trading bot.
Parses arguments, configures logging, and invokes order placement.
"""

import argparse
import os
import sys

# Add project root to path for bot imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env and .env.local into environment (before any credential lookup)
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(".env.local")
except ImportError:
    pass  # python-dotenv optional; env vars can still be set manually

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import format_order_response, format_order_summary, place_order
from bot.validators import ValidationError


def get_env_or_arg(value: str | None, env_var: str) -> str | None:
    """Use value if provided, otherwise read from environment."""
    if value:
        return value
    return os.environ.get(env_var)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trading Bot - Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Market BUY 0.001 BTC
  python cli.py -s BTCUSDT --side BUY -t MARKET -q 0.001

  # Limit SELL 0.01 ETH at 3500
  python cli.py -s ETHUSDT --side SELL -t LIMIT -q 0.01 -p 3500

  # Stop-Limit BUY: trigger at 95000, limit at 94800
  python cli.py -s BTCUSDT --side BUY -t STOP_LIMIT -q 0.002 -p 94800 --stop-price 95000

Environment variables (optional):
  BINANCE_API_KEY     - API key (or use --api-key)
  BINANCE_API_SECRET  - API secret (or use --api-secret)
        """,
    )

    parser.add_argument("-s", "--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="BUY or SELL")
    parser.add_argument("-t", "--type", dest="order_type", required=True, choices=["MARKET", "LIMIT", "STOP_LIMIT"], help="MARKET, LIMIT, or STOP_LIMIT")
    parser.add_argument("-q", "--quantity", required=True, help="Order quantity (e.g. 0.001)")
    parser.add_argument("-p", "--price", default=None, help="Limit price (required for LIMIT and STOP_LIMIT)")
    parser.add_argument("--stop-price", dest="stop_price", default=None, help="Trigger price (required for STOP_LIMIT)")

    parser.add_argument("--api-key", default=None, help="Binance API key (or set BINANCE_API_KEY)")
    parser.add_argument("--api-secret", default=None, help="Binance API secret (or set BINANCE_API_SECRET)")

    parser.add_argument("--log-dir", default="logs", help="Directory for log files (default: logs)")

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_dir=args.log_dir)
    logger = __import__("logging").getLogger("trading_bot")

    # Resolve API credentials
    api_key = get_env_or_arg(args.api_key, "BINANCE_API_KEY")
    api_secret = get_env_or_arg(args.api_secret, "BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("ERROR: API credentials required. Set BINANCE_API_KEY and BINANCE_API_SECRET")
        print("       or pass --api-key and --api-secret.")
        sys.exit(1)

    # Print order request summary (use raw values for display; validation happens in place_order)
    price_val = float(args.price) if args.price and args.order_type in ("LIMIT", "STOP_LIMIT") else None
    stop_val = float(args.stop_price) if args.stop_price and args.order_type == "STOP_LIMIT" else None
    print(format_order_summary(args.symbol, args.side, args.order_type, args.quantity, price_val, stop_val))

    try:
        client = BinanceClient(api_key=api_key, api_secret=api_secret)
        response = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )

        is_algo = "algoId" in response
        print(format_order_response(response, is_algo=is_algo))
        print("SUCCESS: Order placed successfully.")

    except ValidationError as e:
        print(f"VALIDATION ERROR: {e}")
        logger.error("Validation failed: %s", e)
        sys.exit(1)
    except BinanceClientError as e:
        print(f"API ERROR: {e}")
        logger.error("API error: %s", e)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
