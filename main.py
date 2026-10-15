from flask import Flask, render_template, request, redirect, url_for
import os
from supabase import create_client, Client

app = Flask(__name__)

# Подключение к Supabase (позже заменим на твои ключи)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "твой_url")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "твой_ключ")

@app.route('/')
def index():
    # Главная страница автобазара
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add_announcement():
    if request.method == 'POST':
        # Здесь будет логика добавления машины/запчасти
        return redirect(url_for('index'))
    return "Страница добавления объявления"

if __name__ == '__main__':
    app.run(debug=True)
