import os
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# =========================
# BOT TOKEN (ENV SAFE)
# =========================
BOT_TOKEN = os.getenv("8632372730:AAEIax1eUT0SY7ddFg2Q4u3qceAXLKqiVh0")

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
    score = 0
    score += (long - short) * 0.9

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
    else:
        return "🟡 Neutral"

def ai_view(score, long, short, funding):
    if score > 20:
        return f"Bullish bias due to long dominance ({long:.1f}% vs {short:.1f}%) and positive flow reaction."
    elif score < -20:
        return f"Bearish pressure with short dominance ({short:.1f}%) and funding stress impact."
    else:
        return f"Neutral structure. Balanced positioning ({long:.1f}% / {short:.1f}%) and no strong directional edge."

# =========================
# AVANTIS LINK
# =========================
def avantis_link(symbol):
    return f"https://www.avantisfi.com/trade?asset={symbol.replace('USDT','-USD')}"

# =========================
# START MENU
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["📊 VIP Analysis"],
        ["🚀 Trade on Avantis"],
        ["📡 Macro Wire"]
    ]

    await update.message.reply_text(
        "🔥 𝗕𝗔𝗦𝗧𝗜𝗦 𝗧𝗥𝗔𝗗𝗘𝗥 𝗜𝗡𝗧𝗘𝗟𝗟𝗜𝗚𝗘𝗡𝗖𝗘\n\n"
        "⚡ Market Analysis • On-chain Flow • Execution Signals\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Built for precision trading decisions.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# BUILD MESSAGE
# =========================
async def build(symbol):

    sym = normalize_symbol(symbol)

    price_task = get_price(sym)
    funding_task = get_funding(sym)
    oi_task = get_open_interest(sym)
    ls_task = get_long_short_ratio(sym)

    price, funding, oi, (long, short) = await asyncio.gather(
        price_task, funding_task, oi_task, ls_task
    )

    score = ai_score(long, short, funding)
    label = ai_label(score)
    view = ai_view(score, long, short, funding)

    delta = round(long - short, 2)

    trade_url = avantis_link(sym)

    text = f"""
━━━━━━━━━━━━━━━━━━
🪙 ASSET: {symbol.upper()}
━━━━━━━━━━━━━━━━━━

💰 PRICE: ${price}

📊 LONG: {long:.2f}%
📉 SHORT: {short:.2f}%
📊 DELTA: {delta:.2f}%

💸 FUNDING: {funding:.6f}
📦 OPEN INTEREST: {oi:.2f}

━━━━━━━━━━━━━━━━━━
🧠 AI SCORE: {score}/100 {label}

🧠 AI VIEW:
{view}

━━━━━━━━━━━━━━━━━━
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Data", callback_data=f"refresh:{symbol}")],
        [InlineKeyboardButton("🚀 Trade on Avantis", url=trade_url)]
    ])

    return text, keyboard

# =========================
# HANDLE MESSAGE
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    if text == "📊 vip analysis":
        await update.message.reply_text("Send symbol (BTC, ETH, SOL)")

    elif text == "🚀 trade on avantis":
        await update.message.reply_text("Send symbol for trade link")

    elif text == "📡 macro wire":
        await update.message.reply_text("https://t.me/themacrowire")

    else:
        msg, kb = await build(text)
        await update.message.reply_text(msg, reply_markup=kb)

# =========================
# REFRESH CALLBACK
# =========================
async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    symbol = query.data.split(":")[1]

    msg, kb = await build(symbol)
    await query.edit_message_text(msg, reply_markup=kb)

# =========================
# APP
# =========================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(refresh))

print("🔥 BASTIS TRADER INTELLIGENCE RUNNING...")
app.run_polling()
