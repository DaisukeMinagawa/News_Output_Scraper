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
conn: sqlite3.Connection = sqlite3.connect("news_articles.db")
cursor: sqlite3.Cursor = conn.cursor()

# テーブル作成 (id, date, headline, dek, link, article_text)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS propublica_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        headline TEXT,
        dek TEXT,
        link TEXT,
        article_text TEXT
    )
"""
)

# ProPublicaトップページ
url: str = "https://www.propublica.org/"
response: requests.Response = requests.get(url)
response.raise_for_status()

# HTMLパース
soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")

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

# 記事要素取得 (divタグで絞り込み)
article_elements: bs4.element.ResultSet = soup.select(
    "div.story-card.story-card--standard"
)

# 記事データを格納するリスト
articles = []
# スクレイピングした記事の数の初期値
scraping_count = 0
for article in article_elements:
    # 日付取得
    timestamp_tag: bs4.element.Tag = article.find("time", class_="timestamp")
    date_str: str = (
        timestamp_tag["datetime"][:10] if timestamp_tag else datetime.now().strftime("%Y-%m-%d")
    )

    # ヘッドライン取得
    hed_tag: bs4.element.Tag = article.find("h3", class_="story-card__hed")
    headline: str = hed_tag.find("a").text.strip() if hed_tag else "Headline not found"

    # ヘッドラインのリンク先リンクを取得
    link: str = hed_tag.find("a")["href"] if hed_tag else "Link not found"

    # 関連文章取得
    dek_tag: bs4.element.Tag = article.find("p", class_="story-card__dek")
    dek: str = dek_tag.text.strip() if dek_tag else "Dek not found"

    # 記事本文取得
    article_response: requests.Response = requests.get(link)
    article_response.raise_for_status()
    article_soup: BeautifulSoup = BeautifulSoup(article_response.content, "html.parser")

    # opener_textを取得、存在しない場合は空文字列に
    opener_text_element = article_soup.select_one(
        "h2.opener__dek.opener__dek--match-text-column"
    )
    opener_text = opener_text_element.get_text().replace("\t", "").replace("\n", " ") if opener_text_element else ""

    # `<div>`直下の`<p>`要素で`data-pp-blocktype="copy"`属性を持つものを見つける
    paragraphs = article_soup.select('div > p[data-pp-blocktype="copy"]')

    # opener_textとparagraphsのテキストを結合
    article_text = [opener_text.strip()] + [p.get_text() for p in paragraphs]

    # 記事データを辞書形式でリストに追加
    articles.append((date_str, headline, dek, link, " ".join(article_text)))
    scraping_count += 1
    print("Scraping success! " + str(scraping_count))

# ループ後にまとめてDBに登録
cursor.executemany(
    """
    INSERT INTO propublica_articles (date, headline, dek, link, article_text)
    VALUES (?, ?, ?, ?, ?)
""",
    articles,
)
print("Insert success!")

# 変更コミット＆DBクローズ
conn.commit()
conn.close()

print("ProPublicaの記事をデータベースに保存しました！")
