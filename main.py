from flask import Flask, render_template, request, redirect, url_for
import os
from supabase import create_client, Client

app = Flask(__name__)

# Подключение к базе данных Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    # Загружаем объявления из базы данных Supabase
    response = supabase.table("announcements").select("*").execute()
    announcements = response.data if response.data else []
    return render_template('index.html', announcements=announcements)

@app.route('/add', methods=['GET', 'POST'])
def add_announcement():
    if request.method == 'POST':
        # Здесь будет логика добавления объявления в базу
        return redirect(url_for('index'))
    return "Страница добавления оголошення"

if __name__ == '__main__':
    app.run(debug=True)
