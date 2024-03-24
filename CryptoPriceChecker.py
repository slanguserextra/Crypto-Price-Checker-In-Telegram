import requests
import sqlite3
import time

# Замените на свой токен бота Telegram
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# URL API Telegram
BASE_URL = f'https://api.telegram.org/bot{TOKEN}/'

# Создаем подключение к базе данных
conn = sqlite3.connect('crypto_bot.db')
c = conn.cursor()

# Создаем таблицу для хранения избранных криптовалют для каждого пользователя
c.execute('''CREATE TABLE IF NOT EXISTS favorites
             (user_id INTEGER, crypto_symbol TEXT)''')
conn.commit()

# Функция для отправки сообщения через API Telegram
def send_message(chat_id, text):
    url = BASE_URL + 'sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    response = requests.post(url, params=params)
    return response.json()

# Функция для получения курса криптовалюты с Binance API
def get_crypto_price(crypto_symbol):
    binance_api_url = f'https://api.binance.com/api/v3/ticker/price?symbol={crypto_symbol}USDT'
    response = requests.get(binance_api_url)
    data = response.json()
    price = float(data['price'])
    return price

# Функция для добавления криптовалюты в избранное
def add_to_favorites(user_id, crypto_symbol):
    c.execute("INSERT INTO favorites VALUES (?, ?)", (user_id, crypto_symbol))
    conn.commit()

# Функция для удаления криптовалюты из избранного
def remove_from_favorites(user_id, crypto_symbol):
    c.execute("DELETE FROM favorites WHERE user_id=? AND crypto_symbol=?", (user_id, crypto_symbol))
    conn.commit()

# Функция для получения списка избранных криптовалют пользователя
def get_favorites(user_id):
    c.execute("SELECT crypto_symbol FROM favorites WHERE user_id=?", (user_id,))
    return [row[0] for row in c.fetchall()]

# Обработка сообщения от пользователя
def handle_message(message):
    chat_id = message['chat']['id']
    text = message.get('text', '')

    if text.startswith('/favourite'):
        _, crypto_symbol = text.split()
        add_to_favorites(message['from']['id'], crypto_symbol.upper())
        send_message(chat_id, f'Криптовалюта {crypto_symbol.upper()} добавлена в избранное.')

    elif text.startswith('/unfavourite'):
        _, crypto_symbol = text.split()
        remove_from_favorites(message['from']['id'], crypto_symbol.upper())
        send_message(chat_id, f'Криптовалюта {crypto_symbol.upper()} удалена из избранного.')

    elif text == '/myf':
        favorites = get_favorites(message['from']['id'])
        if favorites:
            response_text = 'Ваши избранные криптовалюты:\n'
            for i, crypto_symbol in enumerate(favorites, 1):
                try:
                    price = get_crypto_price(crypto_symbol)
                    response_text += f"{i}. {crypto_symbol} - {price:.3f}$\n"
                except Exception as e:
                    response_text += f"{i}. {crypto_symbol} - ошибка при получении курса\n"
            send_message(chat_id, response_text)
        else:
            send_message(chat_id, 'Ваш список избранных криптовалют пуст.')

    elif text.startswith('/'):
        crypto_symbol = text[1:].upper()  # Убираем "/" из начала сообщения и переводим в верхний регистр
        if crypto_symbol in get_favorites(message['from']['id']):
            try:
                price = get_crypto_price(crypto_symbol)
                send_message(chat_id, f'Курс {crypto_symbol} - {price:.3f}$')
            except Exception as e:
                send_message(chat_id, 'Произошла ошибка при получении курса криптовалюты.')
        else:
            send_message(chat_id, f'Криптовалюта {crypto_symbol} не добавлена в избранное. Добавьте ее с помощью команды /favourite')

# Основная функция
def main():
    update_id = None
    while True:
        try:
            response = requests.get(BASE_URL + 'getUpdates', params={'offset': update_id})
            updates = response.json().get('result')
            if updates:
                for update in updates:
                    handle_message(update['message'])
                    update_id = update['update_id'] + 1
        except Exception as e:
            print("Ошибка при обновлении:", e)
        time.sleep(1)

if __name__ == '__main__':
    main()
