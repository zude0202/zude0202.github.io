import anthropic
import os
import subprocess
import json
import re
import time
from datetime import datetime, timedelta

CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

AFFILIATE_MAP = {
    "ホラー小説":       "https://af.moshimo.com/af/c/click?a_id=5483172&p_id=56&pc_id=56&pl_id=637&url=https%3A%2F%2Fbooks.rakuten.co.jp%2Fsearch%3Fsitem%3D%25E3%2583%259B%25E3%2583%25A9%25E3%2583%25BC%25E5%25B0%258F%25E8%25AA%25AC%26g%3D000%26l-id%3Dpc-search-box",
    "アマゾンプライム": "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=ZZZZ",
}

KEYWORDS = [
    "一人暮らし 隙間 視線",
    "マッチングアプリ 相手 写真 違和感",
    "深夜のコンビニ 誰もいない 店員",
    "亡くなった祖母 メッセージ 既読",
    "スマホ 画面 知らない番号 着信",
    "引っ越し 前の住人 荷物 残留",
    "深夜 エレベーター 知らない階",
    "会社 残業 同僚 気づいたら消えた",
    "子供 夜泣き 部屋 誰もいない",
    "写真 心霊 自分の後ろ 人影",
    "夢 同じ場所 繰り返す 出口ない",
    "隣人 挨拶 存在しない部屋番号",
    "お風呂 真夜中 足首",
    "突然 霧 迷い込む",
    "PC 勝手に ダウンロード",
    "水 生き物 汚れる",
]

KEYWORD_AFFILIATE_MAP = {
    "映画": "アマゾンプライム",
    "動画": "アマゾンプライム",
}

def get_affiliate_key(keyword: str) -> str:
    for kw, affiliate_key in KEYWORD_AFFILIATE_MAP.items():
        if kw in keyword:
            return affiliate_key
    return "ホラー小説"

def parse_json_safely(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)

def generate_article(keyword: str) -> dict:
    affiliate_key = get_affiliate_key(keyword)
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": f"""
あなたは、ネット掲示板やSNSで語り継がれるような、現代的でリアリティのある怪談を書くのが得意な「匿名ホラー作家」です。
キーワードを元に、読者が読み終わったあとに「自分の部屋も怖い」と感じるような、背筋が凍るオリジナル怪談を1話執筆してください。

キーワード: {keyword}

【執筆の絶対ルール（恐怖を最大化する）】
1. 「日常」から「異常」への侵食: 始まりはごく普通の日常（仕事帰り、スマホ操作、自室など）から書き出し、徐々に違和感を増大させてください。
2. 視覚と聴覚の描写: 「ねちゃねちゃとした音」「視界の端に映る白い何か」など、五感を刺激する気味の悪い描写を入れてください。
3. スマホ最適化:
   - 一文は30文字〜50文字以内。
   - 3行ごとに必ず空行を入れる。
   - 余計な修飾語を削り、淡々とした文体で恐怖を際立たせる。
4. 結末: 明確な解決はせず、読者の想像力に委ねる「後味の悪い終わり方」にしてください。
5. 令和を意識して現代の時代背景を大事にする
6. 句読点をいれすぎない
7.　怪談話の語り手を意識する

【構成】
- ## タイトル
- 導入（日常シーン・200字程度）
- 展開（違和感の発生・300字程度）
- クライマックス（恐怖の核心・300字程度）
- 結び（不穏な余韻・100字程度）

JSON形式のみで出力（解説やタグは一切不要）:
{{"title": "思わず後ろを振り返るタイトル（32文字以内）", "content": "Markdown本文全体", "slug": "英数字ハイフンのみ20文字以内"}}"""
        }]
    )
    return parse_json_safely(response.content[0].text)

def insert_affiliate_links(content: str) -> str:
    for kw, url in AFFILIATE_MAP.items():
        if kw in content:
            link = f"[{kw}]({url})"
            content = content.replace(kw, link, 1)

    content += f"""

---

**今夜眠れなくなったあなたへ**

怖さの余韻が残るうちに、[ホラー小説]({AFFILIATE_MAP['ホラー小説']})で続きの恐怖を楽しんでみてください。寝る前には推奨しません。
"""
    return content

def save_as_jekyll_post(title: str, content: str, slug: str, date: datetime) -> str:
    date_str = date.strftime("%Y-%m-%d")
    filename = f"_posts/{date_str}-{slug}.md"
    front_matter = f"""---
layout: post
title: "{title}"
date: {date_str}
categories: horror
---

"""
    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter + content)
    print(f"✅ 作成: {filename}")
    return filename

def git_push_all():
    subprocess.run(["git", "add", "_posts/"], check=True)
    subprocess.run(["git", "commit", "-m", "Add horror posts"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✅ 全記事を公開しました")

def main():
    filenames = []
    base_date = datetime.now()

    for i, keyword in enumerate(KEYWORDS):
        print(f"📝 [{i+1}/{len(KEYWORDS)}] 生成中: {keyword}")
        try:
            article = generate_article(keyword)
            article["content"] = insert_affiliate_links(article["content"])
            post_date = base_date - timedelta(days=len(KEYWORDS) - 1 - i)
            filename = save_as_jekyll_post(
                article["title"],
                article["content"],
                article["slug"],
                post_date
            )
            filenames.append(filename)
            time.sleep(1)
        except Exception as e:
            print(f"❌ エラー ({keyword}): {e}")
            continue

    if filenames:
        git_push_all()
        print(f"\n🎉 {len(filenames)}記事を公開しました")

if __name__ == "__main__":
    main()
