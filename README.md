import os
import sys
import aiohttp
import asyncio

print("BOT TOKEN OK")
        async with session.get(ur
        "BTC": "BTCUSDT",
iku;hi(data.get("lastFundingRate") or 0)NCE_FUTURES}/futures/data/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
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

,hgjjl


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
