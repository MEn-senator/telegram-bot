import os
import sys
import aiohttp
import asyncio

from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


# =========================
# ENV
# =========================
load_dotenv()

BOT_TOKEN = "8632372730:AAEIax1eUT0SY7ddFg2Q4u3qceAXLKqivvvvvh0"

if not BOT_TOKEN:
    print("BOT_TOKEN NOT FOUND")
    sys.exit(1)

print("BOT TOKEN OK")


# =========================
# CONSTANTS
# =========================
BINANCE_FUTURES = "https://fapi.binance.com"


# =========================
# HTTP CLIENT (REUSABLE)
# =========================
session = aiohttp.ClientSession()


async def fetch_json(url):
    try:
        async with session.get(url, timeout=10) as resp:
            return await resp.json()
    except:
        return {}


# =========================
# SYMBOL NORMALIZER
# =========================
def normalize_symbol(symbol: str):
    symbol = symbol.upper().replace("-", "").replace("_", "")

    mapping = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
        "BNB": "BNBUSDT",
        "XRP": "XRPUSDT",
        "DOGE": "DOGEUSDT"
    }

    return mapping.get(symbol, symbol + "USDT")


# =========================
# BINANCE DATA
# =========================
async def get_price(symbol):
    data = await fetch_json(f"{BINANCE_FUTURES}/fapi/v1/ticker/price?symbol={symbol}")
    return float(data.get("price") or 0)


async def get_funding(symbol):
    data = await fetch_json(f"{BINANCE_FUTURES}/fapi/v1/premiumIndex?symbol={symbol}")
    return float(data.get("lastFundingRate") or 0)


async def get_open_interest(symbol):
    data = await fetch_json(f"{BINANCE_FUTURES}/fapi/v1/openInterest?symbol={symbol}")
    return float(data.get("openInterest") or 0)


async def get_long_short(symbol):
    data = await fetch_json(
        f"{BINANCE_FUTURES}/futures/data/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
    )

    if isinstance(data, list) and data:
        item = data[0]
        long = float(item.get("longAccount") or 50)
        short = float(item.get("shortAccount") or 50)
        return long * 100, short * 100

    return 50, 50


# =========================
# AI LOGIC
# =========================
def score(long, short, funding):
    s = (long - short) * 0.9
    s += -8 if funding > 0 else 8
    return round(max(min(s, 100), -100), 2)


def label(s):
    if s >= 20:
        return "Bullish"
    if s <= -20:
        return "Bearish"
    return "Neutral"


# =========================
# LINK
# =========================
def link(symbol):
    return f"https://www.avantisfi.com/trade?asset={symbol.replace('USDT','-USD')}"


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["VIP Analysis"], ["Trade"], ["Macro"]]

    await update.message.reply_text(
        "TRADER BOT ACTIVE",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# BUILD MESSAGE
# =========================
async def build(symbol):

    sym = normalize_symbol(symbol)

    price, funding, oi, (l, s) = await asyncio.gather(
        get_price(sym),
        get_funding(sym),
        get_open_interest(sym),
        get_long_short(sym)
    )

    sc = score(l, s, funding)
    lb = label(sc)

    text = f"""
ASSET: {symbol.upper()}

PRICE: {price}
LONG: {l:.2f}%
SHORT: {s:.2f}%
FUNDING: {funding:.6f}
OI: {oi:.2f}

SCORE: {sc}/100 {lb}
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("TRADE", url=link(sym))]
    ])

    return text, kb


# =========================
# HANDLE
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()

    if text in ["VIP ANALYSIS", "TRADE", "MACRO"]:
        await update.message.reply_text("Send symbol")
        return

    msg, kb = await build(text)
    await update.message.reply_text(msg, reply_markup=kb)


# =========================
# APP
# =========================
app = ApplicationBuilder().token(8632372730:AAEIax1eUT0SY7ddFg2Q4u3qceAXLKqiVh0).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()
