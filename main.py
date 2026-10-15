import os
import time
from flask import Flask, redirect, render_template, request, session, url_for
from supabase import Client, create_client
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "autobazar_super_secret_key_2026"

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
    raw_username = request.form.get("username", "").strip()
    username = raw_username.lower()  # Приводим к нижнему регистру
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not password:
      error = "Заповніть усі поля!"
    else:
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
    raw_username = request.form.get("username", "").strip()
    username = raw_username.lower()  # Приводим к нижнему регистру при входе
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
  if "username" not in session:
    return redirect(url_for("login"))

  if request.method == "POST":
    title = request.form.get("title")
    brand = request.form.get("brand")
    model = request.form.get("model")
    price_uah = request.form.get("price_uah")
    year_val = request.form.get("year")
    mileage = request.form.get("mileage")
    city = request.form.get("city")
    description = request.form.get("description")
    author = session.get("username")

    year = int(year_val) if year_val else None
    if year is None or not (2005 <= year <= 2026):
      return (
          "Помилка: рік випуску повинен бути в межах від 2005 до 2026 року!",
          400,
      )

    photos = request.files.getlist("photos")
    valid_photos = [p for p in photos if p and p.filename != ""]

    image_urls = []
    for photo in valid_photos:
      clean_name = secure_filename(photo.filename) or "car.jpg"
      unique_filename = f"{int(time.time())}_{clean_name}"
      file_bytes = photo.read()

      try:
        supabase.storage.from_("photos").upload(
            unique_filename,
            file_bytes,
            {"file-options": '{"contentType": "image/jpeg", "upsert": true}'},
        )
        public_url = supabase.storage.from_("photos").get_public_url(
            unique_filename
        )
        image_urls.append(public_url)
      except Exception as e:
        print(f"Помилка завантаження фото: {e}")

    image_url_str = ",".join(image_urls)

    try:
      supabase.table("announcements").insert({
          "title": title,
          "brand": brand,
          "model": model,
          "price_uah": float(price_uah) if price_uah else 0,
          "year": year,
          "mileage": int(mileage) if mileage else None,
          "city": city,
          "description": description,
          "image_url": image_url_str,
          "author": author,
          "category": "Автомобілі",
      }).execute()
    except Exception as e:
      return f"Помилка бази даних: {e}", 500

    return redirect(url_for("index"))

  return render_template("add.html")


@app.route("/delete/<int:id>")
def delete_announcement(id):
  if "username" not in session:
    return redirect(url_for("login"))

  res = supabase.table("announcements").select("*").eq("id", id).execute()
  if res.data:
    item = res.data[0]
    if (
        item.get("author") == session["username"]
        or session["username"] == "chikibamboni"
    ):
      supabase.table("announcements").delete().eq("id", id).execute()

  if session["username"] == "chikibamboni":
    return redirect(url_for("admin"))
  return redirect(url_for("index"))


# --- ЧАТИ ТА ПОВІДОМЛЕННЯ ---


@app.route("/messages")
def messages():
  if "username" not in session:
    return redirect(url_for("login"))

  current_user = session["username"]

  sent = (
      supabase.table("messages")
      .select("receiver")
      .eq("sender", current_user)
      .execute()
  )
  received = (
      supabase.table("messages")
      .select("sender")
      .eq("receiver", current_user)
      .execute()
  )

  chat_users = set()
  if sent.data:
    for m in sent.data:
      chat_users.add(m["receiver"])
  if received.data:
    for m in received.data:
      chat_users.add(m["sender"])

  return render_template(
      "messages.html", chat_users=list(chat_users), user=current_user
  )


@app.route("/chat/<username>", methods=["GET", "POST"])
def chat(username):
  if "username" not in session:
    return redirect(url_for("login"))

  current_user = session["username"]

  if request.method == "POST":
    text = request.form.get("text")
    if text and text.strip():
      supabase.table("messages").insert({
          "sender": current_user,
          "receiver": username,
          "text": text.strip(),
      }).execute()
    return redirect(url_for("chat", username=username))

  m1 = (
      supabase.table("messages")
      .select("*")
      .eq("sender", current_user)
      .eq("receiver", username)
      .execute()
  )
  m2 = (
      supabase.table("messages")
      .select("*")
      .eq("sender", username)
      .eq("receiver", current_user)
      .execute()
  )

  all_messages = []
  if m1.data:
    all_messages.extend(m1.data)
  if m2.data:
    all_messages.extend(m2.data)

  all_messages.sort(key=lambda x: x.get("created_at", ""))

  return render_template(
      "chat.html",
      messages=all_messages,
      other_user=username,
      user=current_user,
  )


@app.route("/admin")
def admin():
  if session.get("username") != "chikibamboni":
    return redirect(url_for("index"))

  res = supabase.table("announcements").select("*").execute()
  announcements = res.data if res.data else []
  return render_template(
      "admin.html", announcements=announcements, user=session.get("username")
  )


if __name__ == "__main__":
  app.run(debug=True)
