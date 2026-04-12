import anthropic
import os
import random
import subprocess
import json
from datetime import datetime

CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

AFFILIATE_MAP = {
    "ハンドメイド材料": "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=YYYY",
    "イラスト講座":     "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=ZZZZ",
    "動画編集ソフト":   "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=AAAA",
}

KEYWORDS = [
    "趣味 副業 始め方 おすすめ",
    "ハンドメイド 販売 初心者 稼ぐ",
    "イラスト 副業 未経験 始める",
    "写真 副業 売る方法",
    "動画編集 副業 月5万 やり方",
    "ブログ 趣味 収益化 方法",
    "ゲーム 副業 配信 稼ぐ",
    "手芸 副業 minne 出品",
    "音楽 副業 作曲 販売",
    "料理 副業 レシピ 販売",
]

def generate_article(keyword: str) -> dict:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": f"""日本語のSEOブログ記事をMarkdown形式で書いてください。

ブログテーマ: 趣味を副業にする
キーワード: {keyword}
文字数: 1500〜2000字
構成:
- ## 見出し × 3〜4個
- 各セクション300字程度
- 最後に「まとめ」セクション

条件:
- 読者は「趣味を収益化したい20〜40代」を想定
- 具体的な手順や金額の目安を含める
- 上から目線にならず、寄り添うトーン
- 「{list(AFFILIATE_MAP.keys())[0]}」を本文中に自然な形で1〜2回含める

JSON形式のみで出力（他の文字は一切含めない）:
{{"title": "タイトル（32文字以内、キーワードを含む）", "content": "Markdown本文全体", "slug": "url用スラッグ(英数字ハイフンのみ、20文字以内)"}}"""
        }]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

def insert_affiliate_links(content: str) -> str:
    for kw, url in AFFILIATE_MAP.items():
        if kw in content:
            link = f"[{kw}]({url})"
            content = content.replace(kw, link, 1)
    return content

def save_as_jekyll_post(title: str, content: str, slug: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"_posts/{date_str}-{slug}.md"
    front_matter = f"""---
layout: post
title: "{title}"
date: {date_str}
---

"""
    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter + content)
    print(f"✅ ファイル作成: {filename}")
    return filename

def git_push(filename: str):
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run(["git", "commit", "-m", f"Add post: {filename}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✅ 公開完了")

def main():
    keyword = random.choice(KEYWORDS)
    print(f"📝 生成中: {keyword}")
    article = generate_article(keyword)
    article["content"] = insert_affiliate_links(article["content"])
    filename = save_as_jekyll_post(article["title"], article["content"], article["slug"])
    git_push(filename)

if __name__ == "__main__":
    main()
