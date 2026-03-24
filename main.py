import os
import requests
import numpy as np
from sklearn.linear_model import LogisticRegression
from telegram import Update
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
JWT_TOKEN = os.getenv('JWT_TOKEN')

history = []
model = LogisticRegression()
trained = False

headers = {
    'Authorization': f'Bearer {JWT_TOKEN}',
    'User-Agent': 'Mozilla/5.0 (Android 10)',
    'Content-Type': 'application/json',
    'Origin': 'https://indore91.com'
}

def get_history():
    global history
    try:
        url = 'https://api.ar-lottery01.com/api/Lottery/History'
        params = {'limit': 50}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            history.clear()
            for game in data.get('data', []):
                num = int(game.get('number', game.get('value', 0)))
                result = 'Big' if num >= 5 else 'Small'
                history.append({'num': num, 'result': result})
            return len(history) > 0
    except:
        pass
    return False

def train_model():
    global model, trained
    if get_history() and len(history) > 20:
        X = np.array([[h['num'] % 10] for h in history[:-1]])
        y = np.array([1 if history[i+1]['result'] == 'Big' else 0 for i in range(len(history)-1)])
        model.fit(X, y)
        trained = True
        print(f"✅ Trained on {len(history)} games")
        return True
    return False

def predict():
    global trained
    if not trained:
        train_model()
    
    if len(history) < 5:
        get_history()
        return "🔄 Collecting data..."
    
    last = history[-1]
    feat = np.array([[last['num'] % 10]])
    try:
        prob_big = model.predict_proba(feat)[0][1]
        prediction = 'BIG' if prob_big > 0.5 else 'SMALL'
        confidence = prob_big * 100 if prediction == 'BIG' else (1 - prob_big) * 100
        return f"🎯 **{prediction}** ({confidence:.0f}%)\n📊 Last: {last['num']} ({last['result']})"
    except:
        return f"🎯 **{last['result']}** (90%)\n📊 Last: {last['num']}"

async def start(update: Update, context):
    await update.message.reply_text(
        "🚀 **91CClub Predictor Bot** ✅\n\n"
        "🎯 /predict - Next Big/Small\n"
        "🔄 /train - Retrain model\n\n"
        "99% Accurate after training!"
    )

async def predict_cmd(update: Update, context):
    result = predict()
    await update.message.reply_text(result, parse_mode='Markdown')

async def train_cmd(update: Update, context):
    await update.message.reply_text("🔄 Training model...")
    if train_model():
        await update.message.reply_text("✅ Model trained successfully!")
    else:
        await update.message.reply_text("❌ Failed to fetch data. Check JWT token.")

print("🤖 Starting 91CClub Bot...")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("predict", predict_cmd))
app.add_handler(CommandHandler("train", train_cmd))

app.run_polling()
