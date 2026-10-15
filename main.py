import os
from flask import Flask, redirect, render_template, request, url_for
from supabase import Client, create_client

app = Flask(__name__)

# Подключение к базе данных Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def index():
  # Загружаем объявления из базы данных Supabase
  response = supabase.table("announcements").select("*").execute()
  announcements = response.data if response.data else []
  return render_template("index.html", announcements=announcements)


@app.route("/add", methods=["GET", "POST"])
def add_announcement():
  if request.method == "POST":
    title = request.form.get("title")
    brand = request.form.get("brand")
    model = request.form.get("model")
    price_uah = request.form.get("price_uah")
    year = request.form.get("year")
    mileage = request.form.get("mileage")
    city = request.form.get("city")
    description = request.form.get("description")

    # Получаем список загруженных фотографий
    photos = request.files.getlist("photos")
    valid_photos = [p for p in photos if p and p.filename != ""]

    # Проверка: от 1 до 10 фотографий
    if not (1 <= len(valid_photos) <= 10):
      return (
          "Помилка: потрібно завантажити від 1 до 10 фотографій!",
          400,
      )

    image_urls = []
    for photo in valid_photos:
      filename = photo.filename
      file_bytes = photo.read()
      try:
        # Загружаем фото в хранилище Supabase (бакет 'photos')
        supabase.storage.from_("photos").upload(
            filename, file_bytes, {"file-options": '{"upsert":true}'}
        )
        # Получаем публичную ссылку на фото
        public_url = supabase.storage.from_("photos").get_public_url(filename)
        image_urls.append(public_url)
      except Exception as e:
        print(f"Помилка завантаження фото: {e}")

    # Объединяем ссылки через запятую
    image_url_str = ",".join(image_urls)

    # Сохраняем объявление в таблицу announcements
    supabase.table("announcements").insert({
        "title": title,
        "brand": brand,
        "model": model,
        "price_uah": float(price_uah) if price_uah else 0,
        "year": int(year) if year else None,
        "mileage": int(mileage) if mileage else None,
        "city": city,
        "description": description,
        "image_url": image_url_str,
    }).execute()

    return redirect(url_for("index"))

  return render_template("add.html")


if __name__ == "__main__":
  app.run(debug=True)
