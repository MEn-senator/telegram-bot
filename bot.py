import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
BOT_TOKEN = "8632372730:AAEIax1eUT0SY7ddFg2Q4u3qceAXLKqiVh0"
import os
BOT_TOKEN = os.getenv("8632372730:AAEIax1eUT0SY7ddFg2Q4u3qceAXLKqiVh0")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Example: /check bitcoin")
        return
    
    coin = context.args[0]

    url = f"https://api.coingecko.com/api/v3/coins/{coin}"
    res = requests.get(url).json()

    try:
        volume = res["market_data"]["total_volume"]["usd"]
        market_cap = res["market_data"]["market_cap"]["usd"]
    except:
        await update.message.reply_text("Coin not found ❌")
        return

    if volume > 100000000 and market_cap < 500000000:
        risk = "HIGH 🚨"
    else:
        risk = "LOW ✅"

    msg = f"""
Risk: {risk}
Volume: {volume}
Market Cap: {market_cap}
"""

    await update.message.reply_text(msg)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("check", check))

app.run_polling()
