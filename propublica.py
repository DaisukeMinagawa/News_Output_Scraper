import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import bs4
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
from dotenv import load_dotenv
# データベース接続
conn: sqlite3.Connection = sqlite3.connect('propublica_articles.db')
cursor: sqlite3.Cursor = conn.cursor()

# テーブル作成
cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        headline TEXT,
        dek TEXT
    )
''')

# ProPublicaトップページ
url: str = "https://www.propublica.org/"
response: requests.Response = requests.get(url)
response.raise_for_status()

# HTMLパース
soup: BeautifulSoup = BeautifulSoup(response.content, 'html.parser')

# 記事要素取得（divタグで絞り込み）、もしarticle_elementsが空なら「ウェブサイト構造が変更されました」とエラーを出力して、
# さらに同メッセージをGmailに送信する。
if not soup.select('div.story-card.story-card--standard'):
    print("ウェブサイト構造が変更されました")
    # Gmailの設定を.envファイルから読み込む
    load_dotenv()
    gmail_account: str = os.getenv("GMAIL_ACCOUNT")
    gmail_password: str = os.getenv("GMAIL_PASSWORD")
    to_email: str = os.getenv("TO_EMAIL")
    # メール送信
    msg = MIMEText("ウェブサイト構造が変更されました")
    msg["Subject"] = "ProPublicaスクレイピングエラー"
    msg["From"] = gmail_account
    msg["To"] = to_email
    msg["Date"] = formatdate()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(gmail_account, gmail_password)
    server.send_message(msg)
    server.quit()
    exit()

article_elements: bs4.element.ResultSet = soup.select('div.story-card.story-card--standard')

for article in article_elements:
    # 日付取得
    timestamp_tag: bs4.element.Tag = article.find('time', class_='timestamp')  # class_='timestamp' を追加
    if timestamp_tag:
        date_str: str = timestamp_tag['datetime'][:10]  # datetime属性から日付をYYYY-MM-DD形式で取得
    else:
        date_str: str = datetime.now().strftime('%Y-%m-%d')

    # ヘッドライン取得
    hed_tag: bs4.element.Tag = article.find('h3', class_='story-card__hed')
    headline: str = hed_tag.find('a').text.strip() if hed_tag else "Headline not found"

    # 関連文章取得
    dek_tag: bs4.element.Tag = article.find('p', class_='story-card__dek')
    dek: str = dek_tag.text.strip() if dek_tag else "Dek not found"

    # DB保存
    cursor.execute('''
        INSERT INTO articles (date, headline, dek)
        VALUES (?, ?, ?)
    ''', (date_str, headline, dek))

# 変更コミット＆DBクローズ
conn.commit()
conn.close()

print("ProPublicaの記事をデータベースに保存しました！")