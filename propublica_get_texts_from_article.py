import requests
from bs4 import BeautifulSoup

# 指定されたURLからHTMLコンテンツを取得
url = "https://www.propublica.org/article/cyber-safety-board-never-investigated-solarwinds-breach-microsoft"
response = requests.get(url)
html_content = response.text

# BeautifulSoupを使用してHTMLを解析
soup = BeautifulSoup(html_content, 'html.parser')

# `h2`要素で`opener__dek opener__dek--match-text-column`クラスを持つ要素のテキストを取得
opener_text_element = soup.select_one('h2.opener__dek.opener__dek--match-text-column')
if opener_text_element:
    opener_text = opener_text_element.get_text()
else:
    opener_text = "It is empty."
    print("[" + opener_text + "]")

# `<div>`直下の`<p>`要素で`data-pp-blocktype="copy"`属性を持つものを見つける
paragraphs = soup.select('div > p[data-pp-blocktype="copy"]')

# `opener_text`を`paragraphs`リストの先頭に挿入
# BeautifulSoupのElementオブジェクトではないため、テキストのみを扱う
paragraph_texts = [opener_text.replace("\t", "").replace("\n", "")] + [p.get_text() for p in paragraphs]

# 各要素のテキスト内容を抽出して表示
for text in paragraph_texts:
    print(text)