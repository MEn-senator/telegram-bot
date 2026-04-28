import os
import sys
import aiohttp
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# SAFE ENV CHECK (IMPORTANT)
# =========================
BOT_TOKEN = os.getenv("8632372730:AAEIax1eUT0SY7ddFg2Q4u3qceAXLKqiVh0")

if not BOT_TOKEN or len(BOT_TOKEN) < 20:
    print("❌ BOT_TOKEN is missing or invalid!")
    print("👉 Check Render Environment Variables (BOT_TOKEN)")
    sys.exit(1)

print("✅ BOT TOKEN LOADED SUCCESSFULLY")


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
# BINANCE ENGINE
# =========================
BINANCE_FUTURES = "https://fapi.binance.com"


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


async def get_price(symbol):
    data = await fetch_json(f"{BINANCE_FUTURES}/fapi/v1/ticker/price?symbol={symbol}")
    return float(data.get("price", 0))


async def get_funding(symbol):
    data = await fetch_json(f"{BINANCE_FUTURES}/fapi/v1/premiumIndex?symbol={symbol}")
    return float(data.get("lastFundingRate", 0))


async def get_open_interest(symbol):
    data = await fetch_json(f"{BINANCE_FUTURES}/fapi/v1/openInterest?symbol={symbol}")
    return float(data.get("openInterest", 0))


async def get_long_short_ratio(symbol):
    data = await fetch_json(
        f"{BINANCE_FUTURES}/futures/data/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
    )

    if isinstance(data, list) and len(data) > 0:
        item = data[0]
        long = float(item.get("longAccount", 50))
        short = float(item.get("shortAccount", 50))
        return long * 100, short * 100

    return 50, 50


# =========================
# AI ENGINE
# =========================
def ai_score(long, short, funding):
    score = (long - short) * 0.9

    if funding > 0:
        score -= 8
    else:
        score += 8

    return round(max(min(score, 100), -100), 2)


def ai_label(score):
    if score >= 20:
        return "🟢 Bullish"
    elif score <= -20:
        return "🔴 Bearish"
    return "🟡 Neutral"


def ai_view(score, long, short, funding):
    if score > 20:
        return f"Bullish bias ({long:.1f}% vs {short:.1f}%)"
    elif score < -20:
        return f"Bearish pressure ({short:.1f}%)"
    return f"Neutral structure ({long:.1f}% / {short:.1f}%)"


# =========================
# AVANTIS LINK
# =========================
def avantis_link(symbol):
    return f"https://www.avantisfi.com/trade?asset={symbol.replace('USDT','-USD')}"


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📊 VIP Analysis"],
        ["🚀 Trade on Avantis"],
        ["📡 Macro Wire"]
    ]

    await update.message.reply_text(
        "🔥 BASTIS TRADER INTELLIGENCE\n"
        "━━━━━━━━━━━━━━━━━━",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# BUILD
# =========================
async def build(symbol):

    sym = normalize_symbol(symbol)

    price, funding, oi, (long, short) = await asyncio.gather(
        get_price(sym),
        get_funding(sym),
        get_open_interest(sym),
        get_long_short_ratio(sym)
    )

    score = ai_score(long, short, funding)
    label = ai_label(score)
    view = ai_view(score, long, short, funding)

    trade_url = avantis_link(sym)

    text = f"""
━━━━━━━━━━━━━━━━━━
🪙 ASSET: {symbol.upper()}
━━━━━━━━━━━━━━━━━━

💰 PRICE: ${price}
📊 LONG: {long:.2f}%
📉 SHORT: {short:.2f}%
💸 FUNDING: {funding:.6f}
📦 OI: {oi:.2f}

━━━━━━━━━━━━━━━━━━
🧠 SCORE: {score}/100 {label}

🧠 VIEW:
{view}

━━━━━━━━━━━━━━━━━━
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Trade", url=trade_url)]
    ])

    return text, keyboard


# =========================
# HANDLE
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text == "📊 vip analysis":
        await update.message.reply_text("Send symbol (BTC, ETH, SOL)")
        return

    if text == "🚀 trade on avantis":
        await update.message.reply_text("Send symbol")
        return

    msg, kb = await build(text)
    await update.message.reply_text(msg, reply_markup=kb)


# =========================
# APP
# =========================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🔥 BOT RUNNING...")
app.run_polling()
