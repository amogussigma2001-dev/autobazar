import os
from flask import Flask, redirect, render_template, request, session, url_for
from supabase import Client, create_client

app = Flask(__name__)
app.secret_key = "autobazar_super_secret_key_2026"  # Секретный ключ для сессий

# Подключение к базе данных Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def index():
  response = supabase.table("announcements").select("*").execute()
  announcements = response.data if response.data else []
  return render_template(
      "index.html",
      announcements=announcements,
      user=session.get("username"),
  )


@app.route("/register", methods=["GET", "POST"])
def register():
  error = None
  if request.method == "POST":
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # Проверяем, занят ли юзернейм
    existing = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .execute()
    )
    if existing.data:
      error = "Користувач з таким ім'ям вже існує!"
    else:
      supabase.table("users").insert({
          "username": username,
          "email": email,
          "password": password,
      }).execute()
      session["username"] = username
      return redirect(url_for("index"))

  return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
  error = None
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    res = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .eq("password", password)
        .execute()
    )
    if res.data:
      session["username"] = username
      return redirect(url_for("index"))
    else:
      error = "Невірний логін або пароль!"

  return render_template("login.html", error=error)


@app.route("/logout")
def logout():
  session.pop("username", None)
  return redirect(url_for("index"))


@app.route("/add", methods=["GET", "POST"])
def add_announcement():
  # Если пользователь не вошел в систему — перенаправляем на вход
  if "username" not in session:
    return redirect(url_for("login"))

  if request.method == "POST":
    title = request.form.get("title")
    brand = request.form.get("brand")
    model = request.form.get("model")
    price_uah = request.form.get("price_uah")
    year = request.form.get("year")
    mileage = request.form.get("mileage")
    city = request.form.get("city")
    description = request.form.get("description")
    author = session.get("username")

    photos = request.files.getlist("photos")
    valid_photos = [p for p in photos if p and p.filename != ""]

    if not (1 <= len(valid_photos) <= 10):
      return "Помилка: потрібно завантажити від 1 до 10 фотографій!", 400

    image_urls = []
    for photo in valid_photos:
      filename = photo.filename
      file_bytes = photo.read()
      try:
        supabase.storage.from_("photos").upload(
            filename, file_bytes, {"file-options": '{"upsert":true}'}
        )
        public_url = supabase.storage.from_("photos").get_public_url(filename)
        image_urls.append(public_url)
      except Exception as e:
        print(f"Помилка завантаження фото: {e}")

    image_url_str = ",".join(image_urls)

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
        "author": author,
    }).execute()

    return redirect(url_for("index"))

  return render_template("add.html")


if __name__ == "__main__":
  app.run(debug=True)
