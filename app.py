
from flask import Flask, render_template, request, redirect, url_for, g
from jinja2 import DictLoader
import sqlite3

app = Flask(__name__)
DATABASE = "fix_turba.db"

# ==========================================================
#  РЕКЛАМА: заработок на сайте
#  Чтобы реклама реально работала и приносила деньги:
#  1) сайт должен быть выложен в интернет (хостинг + домен),
#     на localhost (127.0.0.1) показы не засчитываются;
#  2) зарегистрируйся как владелец площадки:
#     - Яндекс РСЯ: partner2.yandex.ru (Рекламная сеть Яндекса)
#     - VK Реклама: ads.vk.com  ->  виджеты для сайтов
#  3) в кабинете получишь HTML-код блока и вставь его ЦЕЛИКОМ
#     в одну из переменных ниже (в кавычки), сохрани и перезапусти.
#  Пока переменные пустые — на странице видно заглушку "Рекламный блок".
# ==========================================================
AD_YANDEX_CODE = ""   # сюда вставь код рекламного блока РСЯ (Яндекс)
AD_VK_CODE = ""       # сюда вставь код виджета VK Рекламы

START_GAMES = [
    ("Geometry Dash",
     "Хардкорный платформер-раннер про кубик, который прыгает через шипы под музыку. Одна ошибка - и всё сначала!",
     150, "geometry_dash.png", "steam://run/322170"),
    ("Counter-Strike 2",
     "Легендарный тактический шутер 5 на 5: заложники, бомба и невероятный скилл. Обновлённая версия CS на движке Source 2.",
     0, "cs2.png", "steam://run/730"),
    ("Hello Neighbor",
     "Стелс-хоррор про соседа, который что-то прячет в подвале. Проберись в его дом и разгадай тайну!",
     349, "hello_neighbor.png", "steam://run/521840"),
]

STYLE = """
    body { margin:0; font-family:Arial,sans-serif; background:#1b2838; color:#c6d4e0; }
    header { background:#171a21; padding:12px 30px; display:flex; align-items:center; gap:30px; }
    .logo { font-size:24px; font-weight:bold; color:#fff; letter-spacing:1px; }
    .logo span { color:#66c0f4; }
    nav a { color:#b8b6b4; text-decoration:none; margin-right:18px; font-size:14px; }
    nav a:hover { color:#fff; }
    .container { max-width:960px; margin:30px auto; padding:0 15px; }
    h1 { color:#fff; font-size:22px; }
    .game-card { display:flex; background:#16202d; margin:12px 0; border-radius:4px; overflow:hidden; text-decoration:none; color:inherit; }
    .game-card:hover { background:#1f3046; }
    .game-card img { width:240px; height:120px; object-fit:cover; }
    .card-body { padding:12px 18px; flex:1; }
    .card-title { color:#fff; font-size:18px; font-weight:bold; }
    .card-desc { font-size:13px; color:#8ba0b4; margin:6px 0; }
    .price-tag { display:inline-block; background:#4c6b22; color:#a4d007; padding:5px 12px; border-radius:3px; font-weight:bold; }
    .price-free { display:inline-block; background:#3d4450; color:#b9e3ff; padding:5px 12px; border-radius:3px; font-weight:bold; }
    .owned-tag { display:inline-block; background:#3d4450; color:#6cc1f7; padding:5px 12px; border-radius:3px; }
    .btn { display:inline-block; background:linear-gradient(135deg,#75b022 0%,#588a1b 100%); color:#fff; border:none;
           padding:10px 40px; border-radius:2px; font-size:16px; cursor:pointer; text-decoration:none; }
    .btn:hover { background:linear-gradient(135deg,#8ec63a 0%,#6ca32a 100%); }
    .btn-play { background:linear-gradient(135deg,#2a6db0 0%,#1b4f8a 100%); }
    .btn-play:hover { background:linear-gradient(135deg,#3b85d1 0%,#2a6db0 100%); }
    .detail img { width:100%; border-radius:4px; }
    input, textarea { background:#101822; border:1px solid #2a3f55; color:#c6d4e0; padding:8px; border-radius:3px; }
    footer { text-align:center; padding:20px; color:#5c7a99; font-size:12px; margin-top:40px; }
    a.blue { color:#66c0f4; }
    /* Рекламные блоки */
    .ad-slot { background:#101822; border:1px dashed #2a3f55; border-radius:4px; margin:18px auto;
               max-width:960px; min-height:90px; display:flex; align-items:center; justify-content:center;
               color:#5c7a99; font-size:13px; text-align:center; padding:10px; }
"""

LAYOUT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Fix_TURBA{% endblock %}</title>
    <style>@@STYLE@@</style>
</head>
<body>
    <header>
        <div class="logo">Fix_<span>TURBA</span></div>
        <nav>
            <a href="{{ url_for('index') }}">Магазин</a>
            <a href="{{ url_for('library') }}">Библиотека</a>
            <a href="{{ url_for('add_game') }}">Добавить игру</a>
        </nav>
    </header>
    <div class="ad-slot ad-top">
        {% if ad_yandex %}{{ ad_yandex|safe }}{% elif ad_vk %}{{ ad_vk|safe }}{% else %}Рекламный блок (верх) — код подключается в РСЯ или VK Рекламе{% endif %}
    </div>
    <div class="container">{% block content %}{% endblock %}</div>
    <div class="ad-slot ad-bottom">
        {% if ad_yandex %}{{ ad_yandex|safe }}{% elif ad_vk %}{{ ad_vk|safe }}{% else %}Рекламный блок (низ) — код подключается в РСЯ или VK Рекламе{% endif %}
    </div>
    <footer>Fix_TURBA © 2026</footer>
</body>
</html>
"""

INDEX = """
{% extends "layout.html" %}
{% block title %}Fix_TURBA — Магазин{% endblock %}
{% block content %}
<h1>Все игры</h1>
{% for game in games %}
<a href="{{ url_for('game_page', game_id=game.id) }}" style="text-decoration:none; color:inherit;">
  <div class="game-card">
    <img src="{{ url_for('static', filename='covers/' + game.cover) }}" alt="{{ game.title }}">
    <div class="card-body">
      <div class="card-title">{{ game.title }}</div>
      <div class="card-desc">{{ game.description }}</div>
      <div>
        {% if game.owned %}
          <span class="owned-tag">✔ В библиотеке</span>
        {% elif game.price == 0 %}
          <span class="price-free">Бесплатно</span>
        {% else %}
          <span class="price-tag">{{ game.price }} ₽</span>
        {% endif %}
      </div>
    </div>
  </div>
</a>
{% endfor %}
{% endblock %}
"""

GAME = """
{% extends "layout.html" %}
{% block title %}Fix_TURBA — {{ game.title }}{% endblock %}
{% block content %}
<div class="detail">
    <h1>{{ game.title }}</h1>
    <img src="{{ url_for('static', filename='covers/' + game.cover) }}" alt="{{ game.title }}">
    <p style="font-size:15px; line-height:1.5;">{{ game.description }}</p>
    {% if game.owned %}
        <span class="owned-tag">✔ Игра уже в библиотеке</span><br><br>
        <a class="btn btn-play" href="{{ url_for('play', game_id=game.id) }}">▶ Играть</a>
    {% elif game.price == 0 %}
        <a class="btn" href="{{ url_for('buy', game_id=game.id) }}">Играть бесплатно</a>
    {% else %}
        <a class="btn" href="{{ url_for('buy', game_id=game.id) }}">Купить за {{ game.price }} ₽</a>
    {% endif %}
    <p><a class="blue" href="{{ url_for('index') }}">← Назад в магазин</a></p>
</div>
{% endblock %}
"""

LIBRARY = """
{% extends "layout.html" %}
{% block title %}Fix_TURBA — Библиотека{% endblock %}
{% block content %}
<h1>Библиотека</h1>
{% for game in games %}
<a href="{{ url_for('game_page', game_id=game.id) }}" style="text-decoration:none; color:inherit;">
  <div class="game-card">
    <img src="{{ url_for('static', filename='covers/' + game.cover) }}" alt="{{ game.title }}">
    <div class="card-body">
      <div class="card-title">{{ game.title }}</div>
      <div class="card-desc">{{ game.description }}</div>
      <a class="btn btn-play" href="{{ url_for('play', game_id=game.id) }}">▶ Играть</a>
    </div>
  </div>
</a>
{% else %}
<p>Библиотека пуста. Купи игру в <a class="blue" href="{{ url_for('index') }}">магазине</a> — и она появится здесь.</p>
{% endfor %}
{% endblock %}
"""

PLAY = """
{% extends "layout.html" %}
{% block title %}Fix_TURBA — Запуск: {{ game.title }}{% endblock %}
{% block content %}
<h1>Запускаем «{{ game.title }}»...</h1>
<p>Если игра не открылась сама — нажми кнопку ещё раз.</p>
<a class="btn btn-play" href="{{ game.launch_url or url_for('game_page', game_id=game.id) }}">▶ Открыть ещё раз</a>
<p><a class="blue" href="{{ url_for('library') }}">← В библиотеку</a></p>
{% endblock %}
"""

ADD_GAME = """
{% extends "layout.html" %}
{% block title %}Fix_TURBA — Добавить игру{% endblock %}
{% block content %}
<h1>Добавить игру</h1>
<form method="post">
    <p><input type="text" name="title" placeholder="Название игры" required style="width:320px;"></p>
    <p><textarea name="description" rows="4" placeholder="Описание" style="width:320px;"></textarea></p>
    <p><input type="number" name="price" min="0" placeholder="Цена (0 — бесплатно)" style="width:320px;"></p>
    <p><input type="text" name="cover" placeholder="Имя файла обложки, например mygame.png" style="width:320px;"></p>
    <p><input type="text" name="launch_url" placeholder="Ссылка запуска, например steam://run/730" style="width:320px;"></p>
    <button type="submit" class="btn">Добавить</button>
</form>
<p><a class="blue" href="{{ url_for('index') }}">← Назад</a></p>
{% endblock %}
"""

app.jinja_loader = DictLoader({
    "layout.html": LAYOUT.replace("@@STYLE@@", STYLE),
    "index.html": INDEX,
    "game.html": GAME,
    "library.html": LIBRARY,
    "play.html": PLAY,
    "add_game.html": ADD_GAME,
})


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.context_processor
def inject_ads():
    return {"ad_yandex": AD_YANDEX_CODE, "ad_vk": AD_VK_CODE}


def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, price INTEGER DEFAULT 0, cover TEXT, owned INTEGER DEFAULT 0, launch_url TEXT)")
    cols = [row[1] for row in db.execute("PRAGMA table_info(games)").fetchall()]
    if "launch_url" not in cols:
        db.execute("ALTER TABLE games ADD COLUMN launch_url TEXT")
    count = db.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    if count == 0:
        for title, desc, price, cover, launch in START_GAMES:
            db.execute("INSERT INTO games (title, description, price, cover, launch_url) VALUES (?, ?, ?, ?, ?)", (title, desc, price, cover, launch))
    db.commit()


@app.route("/")
def index():
    games = get_db().execute("SELECT * FROM games").fetchall()
    return render_template("index.html", games=games)


@app.route("/game/<int:game_id>")
def game_page(game_id):
    game = get_db().execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    if game is None:
        return redirect(url_for("index"))
    return render_template("game.html", game=game)


@app.route("/library")
def library():
    games = get_db().execute("SELECT * FROM games WHERE owned = 1").fetchall()
    return render_template("library.html", games=games)


@app.route("/play/<int:game_id>")
def play(game_id):
    db = get_db()
    game = db.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    if game is None or not game["owned"]:
        return redirect(url_for("game_page", game_id=game_id))
    return render_template("play.html", game=game)


@app.route("/buy/<int:game_id>")
def buy(game_id):
    db = get_db()
    db.execute("UPDATE games SET owned = 1 WHERE id = ?", (game_id,))
    db.commit()
    return redirect(url_for("game_page", game_id=game_id))


@app.route("/add", methods=["GET", "POST"])
def add_game():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        cover = request.form.get("cover", "").strip() or "default.png"
        launch_url = request.form.get("launch_url", "").strip()
        try:
            price = max(0, int(request.form.get("price", "0")))
        except ValueError:
            price = 0
        if title:
            db = get_db()
            db.execute("INSERT INTO games (title, description, price, cover, owned, launch_url) VALUES (?, ?, ?, ?, 1, ?)", (title, description, price, cover, launch_url))
            db.commit()
            return redirect(url_for("index"))
    return render_template("add_game.html")


if __name__ == "__main__":
    with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
