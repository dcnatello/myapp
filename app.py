from flask import Flask, render_template, request, abort
import sqlite3
from parser import init_db, parse_rss
from categories import sources

app = Flask(__name__)
DB_PATH = 'news.db'

def get_categories():
    return [
        "все новости", "политика", "экономика", "мир", "технологии",
        "происшествия", "бизнес", "наука", "общество",
        "спорт", "культура", "здоровье", "авто"
    ]

def get_news_page(page, category=None, per_page=7):
    offset = (page - 1) * per_page
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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

    news_items = cur.fetchall()
    conn.close()

    total_pages = (total_news + per_page - 1) // per_page
    return news_items, total_pages

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    categories = get_categories()
    news, total_pages = get_news_page(page, category="все новости")
    current_category = "все новости"
    return render_template('base.html', news=news, page=page, total_pages=total_pages, current_category=current_category, categories=categories)

@app.route('/<string:category>')
def category_page(category):
    categories = get_categories()
    if category not in categories:
        abort(404)
    page = request.args.get('page', 1, type=int)
    news, total_pages = get_news_page(page, category=category)
    current_category = category
    return render_template('base.html', news=news, page=page, total_pages=total_pages, current_category=current_category, categories=categories)

if __name__ == '__main__':
    init_db()
    for url, category in sources:
        parse_rss(url, category)
    app.run(debug=True)
