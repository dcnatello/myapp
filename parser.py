import sqlite3
import feedparser
import re
from html import unescape
from email.utils import parsedate_to_datetime

DB_PATH = 'news.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            pubDate TEXT,
            link TEXT UNIQUE,
            category TEXT,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_news_to_db(news_item):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO news (title, description, pubDate, link, category, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', news_item)
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def clean_html(html):
    return unescape(re.sub(r'<[^>]+>', '', html))

def fix_date(date):
    try:
        dt = parsedate_to_datetime(date)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ''

def get_image_url(entry):
    if 'media_content' in entry and entry['media_content']:
        return entry['media_content'][0].get('url')
    if 'media_thumbnail' in entry and entry['media_thumbnail']:
        return entry['media_thumbnail'][0].get('url')
    if 'enclosures' in entry:
        for e in entry['enclosures']:
            if e.get('type', '').startswith('image/'):
                return e.get('href')
    description = entry.get('description', '') or ''
    match = re.search(r'<img[^>]+src="([^"]+)"', description)
    if match:
        return unescape(match.group(1))
    return None

def parse_rss(url, category):
    if not url:
        return
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.get('title', '') or ''
        description = clean_html(entry.get('description', '') or '')
        pubdate_raw = entry.get('published', '') or entry.get('updated', '') or ''
        pubdate = fix_date(pubdate_raw) if pubdate_raw else ''
        link = entry.get('link', '') or ''
        image = get_image_url(entry)
        news_item = (title, description, pubdate, link, category, image)
        save_news_to_db(news_item)
