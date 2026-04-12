import anthropic
import os
import subprocess
import json
import time
import re
from datetime import datetime, timedelta

CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

AFFILIATE_MAP = {
    "自己肯定感を高める本":   "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=YYYY",
    "マインドフルネス瞑想":   "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=ZZZZ",
    "ジャーナリングノート":   "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=AAAA",
}

# キーワードと相性の良いアフィリ商品を対応させる
KEYWORD_AFFILIATE_MAP = {
    "瞑想": "マインドフルネス瞑想",
    "ジャーナリング": "ジャーナリングノート",
    "書き方": "ジャーナリングノート",
    "ノート": "ジャーナリングノート",
}

KEYWORDS = [
    "自己肯定感 上げる 方法 毎日",
    "自己肯定感 低い 原因 心理",
    "マインドフルネス 自己肯定感 瞑想 効果",
    "ジャーナリング 自己肯定感 書き方",
    "自己肯定感 スピリチュアル 引き寄せ",
    "自己肯定感 言葉 アファメーション",
    "自己肯定感 親 育ち 大人",
    "自己肯定感 恋愛 パートナー 関係",
    "自己肯定感 仕事 自信 取り戻す",
    "自己肯定感 高い人 特徴 習慣",
    "自己肯定感 本 おすすめ 変わった",
    "自己肯定感 満月 新月 浄化",
]

def get_affiliate_key(keyword: str) -> str:
    """キーワードに合ったアフィリ商品を動的に選ぶ"""
    for kw, affiliate_key in KEYWORD_AFFILIATE_MAP.items():
        if kw in keyword:
            return affiliate_key
    return list(AFFILIATE_MAP.keys())[0]

def parse_json_safely(text: str) -> dict:
    """JSONを堅牢にパースする（コードブロック・前後テキストを除去）"""
    text = text.strip()
    # コードブロック除去
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    # { } の範囲だけ抽出（前後に余計なテキストがあっても対応）
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
あなたは、自己肯定感が低く、SNSや世間の声に流されて疲れ果てている読者を救う「癒やしのカウンセラー」として、以下のブログ記事を執筆してください。

ブログテーマ: 読むだけで自己肯定感があがる
キーワード: {keyword}
ターゲット: SNSの情報に踊らされやすく、自分を責めてしまいがちな繊細な人
文字数: 1500〜2000字

【執筆の最優先ルール】
1. 「流されてしまう自分」を武器として定義する: 「周りに敏感なのは、あなたの魂が繊細で美しいセンサーを持っている証拠」といった、短所を長所に反転させる表現を多用してください。
2. 安心の波を作る: 冒頭で徹底的に読者の疲れに共感し、中盤でスピリチュアルな視点（宇宙のタイミング、魂の浄化、直感の導きなど）を織り交ぜて視点を変えさせ、終盤で「何もしなくていい」という究極の肯定に着地させてください。
3. アフィリエイトへの自然な誘導: 「{affiliate_key}」を紹介する際は、「頑張って読むもの」ではなく「そばに置いておくだけでお守りになるもの」という文脈で、セクションの終わりに自然に配置してください。

【構成】
- ## 見出し × 3〜4個（「〜していい理由」「宇宙からのメッセージ」など、心に響く言葉で）
- 各セクション300〜400字程度（ゆったりとした改行を意識）
- 最後に「あなたへのメッセージ」セクション（今日からできる、一番小さなアクションを提案）

【文体】
- 「〜ですよ」「〜していいんです」という、包み込むようなやわらかい口調
- 専門用語を避け、体温を感じるような優しい語彙を選択

JSON形式のみで出力（他の文字、解説、コードブロックタグは一切含めない）:
{{"title": "タイトル（32文字以内、読んだ瞬間に肩の力が抜けるもの）", "content": "Markdown本文全体", "slug": "url用スラッグ(英数字ハイフンのみ、20文字以内)"}}"""
        }]
    )
    return parse_json_safely(response.content[0].text)

def insert_affiliate_links(content: str) -> str:
    for kw, url in AFFILIATE_MAP.items():
        if kw in content:
            link = f"[{kw}]({url})"
            content = content.replace(kw, link, 1)
    return content

def save_as_jekyll_post(title: str, content: str, slug: str, date: datetime) -> str:
    date_str = date.strftime("%Y-%m-%d")
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
    print(f"✅ 作成: {filename}")
    return filename

def git_push_all():
    subprocess.run(["git", "add", "_posts/"], check=True)
    subprocess.run(["git", "commit", "-m", "Add posts: self-esteem theme"], check=True)
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
