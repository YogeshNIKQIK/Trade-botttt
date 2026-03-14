# Trading Bot - Binance Futures Testnet

A Python application for placing **Market**, **Limit**, and **Stop-Limit** orders on **Binance Futures Testnet (USDT-M)**. Built with a clean, layered architecture, structured logging, and robust error handling.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Test Commands](#test-commands)
- [Project Structure](#project-structure)
- [Assumptions & Notes](#assumptions--notes)

---

## Features

- **Order types**: MARKET, LIMIT, STOP_LIMIT (BUY / SELL)
- **Validation**: Symbol, side, type, quantity, price, stop-price
- **Error handling**: Invalid input, API errors, network failures
- **Logging**: API requests, responses, and errors to daily log files
- **Credentials**: Environment variables (`.env`, `.env.local`) or CLI arguments

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLI (cli.py)                                │
│  • Argument parsing (argparse)                                           │
│  • Credential resolution (env / .env.local / CLI)                        │
│  • Orchestrates flow and prints output                                   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Orders Layer (orders.py)                        │
│  • Validates all inputs via validators                                   │
│  • Calls Binance client to place order                                   │
│  • Formats request summary and API response for display                  │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
┌───────────────────────────────┐   ┌──────────────────────────────────────┐
│   Validators (validators.py)  │   │     Client (client.py)                │
│   • Symbol (USDT-M)           │   │   • REST + HMAC SHA256 auth           │
│   • Side (BUY/SELL)           │   │   • /fapi/v1/order (MARKET, LIMIT)    │
│   • Order type                │   │   • /fapi/v1/algoOrder (STOP_LIMIT)   │
│   • Quantity, price           │   └──────────────────────────────────────┘
│   • Stop price                │
└───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Logging (logging_config.py)                           │
│  • File: logs/trading_bot_YYYYMMDD.log                                   │
│  • Console: INFO level                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Flow**:
1. `cli.py` parses arguments, loads credentials from `.env`/`.env.local` or env vars
2. `orders.place_order()` validates inputs via `validators.validate_all()`
3. `client.place_order()` sends request to Binance (REST order or Algo order API)
4. Response is formatted and printed to the user

---

## Prerequisites

- **Python 3.8+**
- **Binance Futures Testnet** account and API credentials

### Binance Testnet Setup

1. Register at [Binance Futures Testnet](https://testnet.binancefuture.com)
2. Go to **API Management** and generate API key and secret
3. Ensure futures trading permissions are enabled

---

## Installation

```bash
# Navigate to project directory
cd trading_bot

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Windows (CMD)
# .venv\Scripts\activate.bat
# Linux / macOS
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

### Credentials

**Option A: `.env` or `.env.local` (recommended)**

Create a file named `.env` or `.env.local` in the `trading_bot` directory:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

**Option B: Environment variables**

```powershell
# Windows (PowerShell)
$env:BINANCE_API_KEY = "your_api_key"
$env:BINANCE_API_SECRET = "your_api_secret"
```

```bash
# Linux / macOS
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
```

**Option C: CLI arguments** (not recommended for shared environments)

Use `--api-key` and `--api-secret`.

---

## Usage

Run the CLI from the `trading_bot` directory:

```bash
python cli.py -s SYMBOL --side BUY --type ORDER_TYPE -q QUANTITY [-p PRICE] [--stop-price TRIGGER_PRICE]
```

### Parameters

| Parameter    | Short | Required              | Description                                |
|-------------|-------|------------------------|--------------------------------------------|
| `--symbol`  | `-s`  | Yes                   | Trading pair (e.g. BTCUSDT, ETHUSDT)       |
| `--side`    | -     | Yes                   | `BUY` or `SELL`                            |
| `--type`    | `-t`  | Yes                   | `MARKET`, `LIMIT`, or `STOP_LIMIT`         |
| `--quantity`| `-q`  | Yes                   | Order quantity                             |
| `--price`   | `-p`  | For LIMIT, STOP_LIMIT | Limit price                                |
| `--stop-price` | -  | For STOP_LIMIT        | Trigger price                              |
| `--log-dir` | -     | No                    | Log directory (default: `logs`)            |

---

## Test Commands

Run these commands from the `trading_bot` directory after installing dependencies and setting credentials.

### MARKET Orders

```bash
python cli.py -s BTCUSDT --side BUY -t MARKET -q 0.01
python cli.py -s BTCUSDT --side SELL -t MARKET -q 0.01
```

### LIMIT Orders

```bash
python cli.py -s BTCUSDT --side BUY -t LIMIT -q 0.01 -p 60000
python cli.py -s BTCUSDT --side SELL -t LIMIT -q 0.01 -p 100000
```

### STOP_LIMIT Orders

Trigger rules:
- **BUY**: Trigger when price **≥** stop-price (stop-price must be **above** current price)
- **SELL**: Trigger when price **≤** stop-price (stop-price must be **below** current price)

```bash
# BUY when BTC reaches 98000, limit at 97500 (current price must be < 98000)
python cli.py -s BTCUSDT --side BUY -t STOP_LIMIT -q 0.01 -p 97500 --stop-price 98000

# SELL when BTC drops to 60000, limit at 60000 (current price must be > 60000)
python cli.py -s BTCUSDT --side SELL -t STOP_LIMIT -q 0.01 -p 60000 --stop-price 60000
```

### Validation Tests (expect errors)

```bash
# Missing price for LIMIT
python cli.py -s BTCUSDT --side BUY -t LIMIT -q 0.01

# Missing stop-price for STOP_LIMIT
python cli.py -s BTCUSDT --side BUY -t STOP_LIMIT -q 0.01 -p 97500

# Invalid symbol
python cli.py -s INVALID --side BUY -t MARKET -q 0.01
```

### Test Summary Table

| Order Type | Side | Command |
|------------|------|---------|
| MARKET | BUY  | `python cli.py -s BTCUSDT --side BUY -t MARKET -q 0.01` |
| MARKET | SELL | `python cli.py -s BTCUSDT --side SELL -t MARKET -q 0.01` |
| LIMIT  | BUY  | `python cli.py -s BTCUSDT --side BUY -t LIMIT -q 0.01 -p 60000` |
| LIMIT  | SELL | `python cli.py -s BTCUSDT --side SELL -t LIMIT -q 0.01 -p 100000` |
| STOP_LIMIT | BUY  | `python cli.py -s BTCUSDT --side BUY -t STOP_LIMIT -q 0.01 -p 97500 --stop-price 98000` |
| STOP_LIMIT | SELL | `python cli.py -s BTCUSDT --side SELL -t STOP_LIMIT -q 0.01 -p 60000 --stop-price 60000` |

> **Note:** Notional (quantity × price) must be **≥ 100 USDT** for all orders. Adjust quantity or use a cheaper symbol (e.g. ETHUSDT, BNBUSDT) if needed.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py       # Package init, version
│   ├── client.py         # Binance API client (REST + HMAC SHA256)
│   ├── orders.py         # Order placement, validation orchestration, formatting
│   ├── validators.py     # Input validation (symbol, side, type, quantity, price)
│   └── logging_config.py # Logging setup (file + console)
├── cli.py                # CLI entry point (argparse)
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── .env.example          # Example credential template (optional)
└── logs/                 # Log files (created at runtime)
    └── trading_bot_YYYYMMDD.log
```

---

## Assumptions & Notes

- **USDT-M only**: Symbols must end with `USDT`
- **Base URL**: `https://testnet.binancefuture.com` (testnet)
- **Time in Force**: GTC (Good Till Cancel) for LIMIT and STOP_LIMIT
- **Position Mode**: Default one-way mode (BOTH)
- **Stop-Limit**: Uses Binance Algo Order API (`/fapi/v1/algoOrder`)

### Logging

- Logs: `logs/trading_bot_YYYYMMDD.log`
- Includes: API requests, responses, validation errors, network errors

### Error Handling

- **ValidationError**: Invalid symbol, side, type, quantity, price, or stop-price
- **BinanceClientError**: API errors (auth, balance, rate limits, trigger conditions)
- **Network**: Timeouts and connection failures
