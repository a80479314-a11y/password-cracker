from flask import Flask, render_template, request, jsonify
import time
from datetime import datetime
import webbrowser
import threading

app = Flask(__name__)
history = []  # Сюда будем складывать результаты проверок

# Загружаем базу паролей из файла
def load_passwords():
    try:
        with open('passwords.txt', 'r', encoding='utf-8') as f:
            # Читаем все строки и убираем символы переноса строки
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("ВНИМАНИЕ: Файл passwords.txt не найден! Используем пустой список.")
        return []

COMMON_PASSWORDS = load_passwords()


def calculate_bruteforce_time(password):
    charset_size = 0
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    if has_lower: charset_size += 26
    if has_upper: charset_size += 26
    if has_digit: charset_size += 10
    if has_special: charset_size += 32

    if charset_size == 0:
        return 0

    combinations = charset_size ** len(password)
    attempts_per_second = 10_000_000_000
    return combinations / attempts_per_second


def format_time(seconds):
    if seconds < 0.001:
        return "Мгновенно"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} миллисекунд"
    elif seconds < 60:
        return f"{seconds:.2f} секунд"
    elif seconds < 3600:
        return f"{seconds / 60:.2f} минут"
    elif seconds < 86400:
        return f"{seconds / 3600:.2f} часов"
    elif seconds < 31536000:
        return f"{seconds / 86400:.2f} дней"
    elif seconds < 31536000 * 100:
        return f"{seconds / 31536000:.2f} лет"
    else:
        return f"{seconds / 31536000:.2e} лет"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check', methods=['POST'])
def check():
    data = request.json
    password = data.get('password', '')

    if not password:
        return jsonify({"error": "Пароль пустой"})

    start_time = time.time()
    found_in_dict = False
    attempts = 0

    for p in COMMON_PASSWORDS:
        attempts += 1
        if p == password:
            found_in_dict = True
            break

    dict_time = time.time() - start_time
    brute_seconds = calculate_bruteforce_time(password)

    if len(password) < 6 or found_in_dict:
        rating = "КРИТИЧЕСКИЙ"
        color = "#ff3333"
    elif len(password) < 8:
        rating = "СЛАБЫЙ"
        color = "#ff9900"
    elif brute_seconds < 31536000:
        rating = "СРЕДНИЙ"
        color = "#ffcc00"
    elif brute_seconds < 31536000 * 100:
        rating = "НАДЕЖНЫЙ"
        color = "#33ff33"
    else:
        rating = "КРЕПОСТЬ"
        color = "#00ffff"

    # Сохраняем в историю
    history.insert(0, {
        "masked": "*" * len(password),
        "rating": rating,
        "color": color,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    if len(history) > 5:
        history.pop()

    return jsonify({
        "found_in_dict": found_in_dict,
        "dict_time": dict_time,
        "brute_seconds": brute_seconds,
        "brute_formatted": format_time(brute_seconds),
        "rating": rating,
        "color": color,
        "attempts": attempts,
        "history": history
    })


def open_browser():
    # Ждем секунду, чтобы сервер успел запуститься, и открываем браузер
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Запускаем открытие браузера в отдельном потоке
    threading.Thread(target=open_browser).start()
    # Запускаем сервер
    app.run(debug=False, port=5000)