# bot.py - Diablo Prediction Bot
import logging
import aiohttp
import sqlite3
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== TOKEN ====================
TOKEN = "8723966859:AAFeTtafFUz_ySZIWyHpYLQMycVOmw-Ij4U"
API_URL = 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'

# ==================== SETUP ====================
logging.basicConfig(level=logging.INFO)
db = sqlite3.connect('predictions.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS predictions 
    (period TEXT PRIMARY KEY, prediction TEXT, actual TEXT, status TEXT, time TIMESTAMP)''')

# ==================== COMMANDS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *DIABLO BOT ACTIVE*\n\n"
        "/predict - Latest prediction\n"
        "/result - Last result\n"
        "/history - Last 5",
        parse_mode='Markdown'
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔮 *Fetching prediction...*", parse_mode='Markdown')
    await asyncio.sleep(1)
    
    # Demo prediction (API se actual data aayega)
    period = datetime.now().strftime("%Y%m%d%H%M") + "M"
    pred = "BIG"
    
    db.execute("INSERT OR REPLACE INTO predictions VALUES (?,?,?,?,?)",
              (period, pred, None, None, datetime.now()))
    db.commit()
    
    await update.message.reply_text(
        f"🎯 *PREDICTION*\n\n"
        f"📌 Period: `{period[-8:]}`\n"
        f"🔮 Prediction: *{pred}*\n"
        f"⏳ Status: Pending",
        parse_mode='Markdown'
    )

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = db.execute("SELECT * FROM predictions ORDER BY time DESC LIMIT 1").fetchone()
    if last and last[3]:
        period, pred, actual, status, _ = last
        icon = "✅" if status == "WIN" else "❌"
        await update.message.reply_text(
            f"📊 *RESULT*\n\n"
            f"📌 Period: `{period[-8:]}`\n"
            f"🔮 Prediction: {pred}\n"
            f"🎲 Actual: {actual}\n"
            f"📈 Result: {icon} {status}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("⏳ No result yet")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.execute("SELECT * FROM predictions ORDER BY time DESC LIMIT 5").fetchall()
    if not rows:
        await update.message.reply_text("📜 No history")
        return
    
    msg = "📜 *HISTORY*\n"
    for i, (period, pred, actual, status, _) in enumerate(rows, 1):
        if actual:
            icon = "✅" if status == "WIN" else "❌"
            result = f"{icon} {actual}"
        else:
            result = "⏳"
        msg += f"\n{i}. `{period[-8:]}`: {pred} → {result}"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== BACKGROUND TASK ====================
async def update_data():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}?t={int(datetime.now().timestamp())}") as resp:
                    data = await resp.json()
                    items = data.get('data', {}).get('list', [])
                    
                    for item in items[:5]:
                        period = item.get('issueNumber')
                        num = int(item.get('number', 0))
                        actual = 'BIG' if num >= 5 else 'SMALL'
                        
                        cur = db.execute("SELECT prediction FROM predictions WHERE period=?", (period,))
                        pred_row = cur.fetchone()
                        
                        if pred_row:
                            status = 'WIN' if pred_row[0] == actual else 'LOSS'
                            db.execute("UPDATE predictions SET actual=?, status=? WHERE period=?", 
                                      (actual, status, period))
                            db.commit()
        except:
            pass
        await asyncio.sleep(10)

# ==================== MAIN ====================
def main():
    print("🤖 Bot starting...")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(CommandHandler("history", history))
    
    # Background task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(update_data())
    
    print("✅ Bot is running!")
    app.run_polling()

if __name__ == '__main__':
    main()
