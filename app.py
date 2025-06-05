from flask import Flask, render_template, request, abort # для создания приложения рендеринга штмл шаблона обработки шттп запроса и обработки ошибок
import sqlite3 # импорт бд
from parser import init_db, parse_rss
from categories import sources
from apscheduler.schedulers.background import BackgroundScheduler # планировщик задач для обновление новостей


app = Flask(__name__) 
DB_PATH = 'news.db' 


def get_categories(): 
    return [
        "все новости", "политика", "экономика", "мир", "технологии",
        "происшествия", "бизнес", "наука", "общество",
        "спорт", "культура", "здоровье", "авто"
    ]


def get_news_page(page, category=None, per_page=7): # возвращает список новостей на странице
    offset = (page - 1) * per_page # смещение для скуель запроса
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # ответ будет в виде словарей а не кортежем (позволяет обращатся к элементам по названию а не индексу)
    cur = conn.cursor()
    
    if category is None or category == "все новости":
        cur.execute('SELECT COUNT(*) FROM news')
        total_news = cur.fetchone()[0]
        cur.execute('''
            SELECT id, title, description, pubDate, link, category, image
            FROM news
            ORDER BY pubDate DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

    else:
        cur.execute('SELECT COUNT(*) FROM news WHERE category = ?', (category,))
        total_news = cur.fetchone()[0]

        cur.execute('''
            SELECT id, title, description, pubDate, link, category, image
            FROM news
            WHERE category = ?
            ORDER BY pubDate DESC
            LIMIT ? OFFSET ?
        ''', (category, per_page, offset))

    news_items = cur.fetchall() # перекидываем результаты в список новостей
    conn.close()
  
    total_pages = (total_news + per_page - 1) // per_page
    return news_items, total_pages 


def update_news():
    for url, category in sources:
        parse_rss(url, category)


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int) # номер страницы из урл
    categories = get_categories()

    news, total_pages = get_news_page(page, category="все новости") # новости для главной страницы
    current_category = "все новости"
    
    return render_template('base.html', news=news, page=page,
                           total_pages=total_pages,
                           current_category=current_category,
                           categories=categories)


@app.route('/<string:category>')
def category_page(category):
    categories = get_categories()
    if category not in categories:
        abort(404)
        
    page = request.args.get('page', 1, type=int) # номер страницы из урл
    news, total_pages = get_news_page(page, category=category) # новости для страницы
    current_category = category

    return render_template('base.html', news=news, page=page,
                           total_pages=total_pages,
                           current_category=current_category,
                           categories=categories)


if __name__ == '__main__':
    init_db()
    update_news()
    
    scheduler = BackgroundScheduler() # создание планировщика задач
    scheduler.add_job(update_news, 'interval', minutes=5)
    scheduler.start()

    app.run(debug=True)

