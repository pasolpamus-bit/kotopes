import time
import telebot
import threading
from tqdm import tqdm
from database import Database
from scanner import HybridScanner

# --- КОНФИГУРАЦИЯ ---
TOKEN = '8576232768:AAELYzpC-uRJkXU8-xYGmFJO0bLT3oq7I1o'
HELIUS_URL = 'https://mainnet.helius-rpc.com/?api-key=5837dad1-71e6-40d4-9c81-b82fb8f41f14'
# ---------------------

bot = telebot.TeleBot(TOKEN)
db = Database()
scanner = HybridScanner(HELIUS_URL)
active_chat_id = None
monitored_assets = {}

@bot.message_handler(commands=['start'])
def start(message):
    global active_chat_id
    active_chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Найти контракты Bybit", "🐋 Запустить слежку (15-30%)")
    bot.send_message(active_chat_id, "🚀 Бот готов. Нажмите 'Найти контракты' для старта.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔍 Найти контракты Bybit")
def find_assets(message):
    global monitored_assets
    bot.send_message(message.chat.id, "🛰 Связываюсь с Bybit...")
    
    symbols = scanner.get_bybit_futures_list()
    
    if not symbols:
        bot.send_message(message.chat.id, "❌ Ошибка: Не удалось получить список пар от Bybit. Попробуйте позже.")
        print("[!] Список пар пуст. Проверьте headers или доступ к сети.")
        return

    print(f"\n[BYBIT] Найдено подходящих пар: {len(symbols)}")
    bot.send_message(message.chat.id, f"✅ Найдено {len(symbols)} пар. Ищу их контракты в Solana...")
    
    # Обрабатываем топ-50 волатильных пар
    for s in tqdm(symbols[:50], desc="Поиск контрактов"):
        addr = scanner.get_solana_contract(s)
        if addr:
            monitored_assets[s] = addr
            holders = scanner.get_top_holders(addr)
            for h in holders:
                db.update_holder(s, addr, h['address'], float(h['amount']))
        time.sleep(0.5)

    if monitored_assets:
        bot.send_message(message.chat.id, f"💎 Готово! Слежу за: {', '.join(monitored_assets.keys())}")
    else:
        bot.send_message(message.chat.id, "⚠️ Контракты в сети Solana не найдены.")

def monitoring_loop():
    global active_chat_id
    while True:
        if monitored_assets and active_chat_id:
            print(f"\n[{time.strftime('%H:%M:%S')}] Сверка балансов китов...")
            for symbol, addr in monitored_assets.items():
                holders = scanner.get_top_holders(addr)
                for h in holders:
                    wallet = h['address']
                    new_bal = float(h['amount'])
                    data = db.get_holder_data(addr, wallet)
                    
                    if data:
                        old_bal, _ = data
                        if old_bal > 0:
                            diff = ((new_bal - old_bal) / old_bal) * 100
                            if 15 <= abs(diff) <= 30:
                                emoji = "📈 ЗАКУП" if diff > 0 else "📉 СЛИВ"
                                bot.send_message(active_chat_id, f"🐋 Кит {symbol}: {emoji} на {abs(diff):.1f}%\n`{wallet}`")
                    
                    db.update_holder(symbol, addr, wallet, new_bal)
                time.sleep(0.5)
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=monitoring_loop, daemon=True).start()
    print("🚀 Бот запущен. Ожидаю нажатия кнопки в Telegram...")
    bot.polling(none_stop=True)