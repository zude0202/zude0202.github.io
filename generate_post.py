import anthropic
import os
import subprocess
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

AFFILIATE_MAP = {
    "ホラー小説":       "https://af.moshimo.com/af/c/click?a_id=5483172&p_id=56&pc_id=56&pl_id=637&url=https%3A%2F%2Fbooks.rakuten.co.jp%2Fsearch%3Fsitem%3D%25E3%2583%259B%25E3%2583%25A9%25E3%2583%25BC%25E5%25B0%258F%25E8%25AA%25AC%26g%3D000%26l-id%3Dpc-search-box",
    "アマゾンプライム": "https://af.moshimo.com/af/c/click?a_id=XXXX&p_id=ZZZZ",
}

KEYWORDS = [
    # デジタル・テクノロジー系
    "身に覚えのないログイン通知",
    "予測変換の暴走",
    "履歴にない検索ワード",
    "ノイズ混じりのボイスチャット",
    "低画質の映り込み",
    "非公開のはずの住所",
    "知らないグループチャットへの招待",
    "同期された見知らぬ写真",
    "GPSの現在地のズレ",
    "深夜の無言着信",
    "幻聴の通知音",
    "削除できないアプリ",
    "自分を監視しているアカウント",
    "他人のIDでのログイン",
    "SNSの裏垢特定",
    "ネット掲示板の予言",

    # 生活・都市空間系
    "昨日までなかった路地",
    "空き家のWi-Fi",
    "深夜のスマートスピーカーの応答",
    "誰もいないはずの隣室の足音",
    "防犯カメラの死角",
    "オートロックの誤作動",
    "不自然に安いレンタルオフィス",
    "集合ポストの宛先不明",
    "深夜のコインランドリー",
    "非常階段の落とし物",
    "ルールが変わったゴミ出し",
    "隣人の異常な生活音",
    "繰り返される街頭放送",
    "宅配便の中身不明",

    # 身体・知覚・記憶系
    "鏡の中の数秒遅れる動き",
    "記憶にない痣",
    "視界の端を横切る黒い影",
    "デジャヴの連続",
    "自分によく似た通行人",
    "味のしない食事",
    "誰かに見られている感覚",
    "寝言で話す知らない名前",
    "体温の急激な低下",
    "顔が思い出せない知人",
    "偽の記憶",

    # 社会・制度系
    "名前が書き換えられた名簿",
    "自分だけが覚えている店",
    "宛先の間違った遺書",
    "古いSDカードの中身",
    "生活のルーチン化",
    "隠しカメラの存在",
    "偽の身分証",
    "改ざんされた契約書",
    "現実のバグ",
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
あなたは怪談作家です。以下の文体的特徴を完全に体現した怪談を執筆してください。

キーワード: {keyword}

【文体の絶対条件】

■ 語り手の立ち位置
- 一人称「私」で語るが、恐怖に対して過剰に反応しない
- 「そこに在ったもの」を正確に写し取ろうとする、冷めた手触りを維持する
- 丁寧な語り口の中に「……だろうか」「……だったのだ」という突き放した断定を混ぜる

■ 【改行の絶対ルール】
- 句点「。」のたびに必ず改行する
- 1行は絶対に25文字を超えない
- 意味の切れ目で空行を入れる

■ 語彙・表現
- 触覚・嗅覚・聴覚への固執（「ねちゃりとした音」「喉の奥に詰まるような」）
- 「〜という。」の伝聞形式を要所で使い、逃れられない事実感を出す
- 日常がある一瞬で異界に変わる瞬間を静かなトーンで描く

■ 恐怖の構造
- 怪異の「理由」は絶対に説明しない
- 全体像ではなく「指先が少し長かった」のような異様な細部を執拗に描写する
- 最後の一行で、怪異が「今これを読んでいるあなた」のそばにいることを示唆して終わる
- 解決しない。浄化しない。ただ「残る」

【構成】
- タイトル（読んだ瞬間に嫌な予感がするもの・32文字以内）
- 導入（完全な日常・150字程度）
- 展開（最初の違和感・細部への固執・250字程度）
- クライマックス（世界の前提が崩れる瞬間・250字程度）
- 結び（解決しない余韻・最後の一行で読者に「残す」・100字程度）
- ただし「導入」「展開」「クライマックス」「結び」という見出しは絶対に本文に入れないこと。
  見出し（##、###）は使わない。
  段落と改行だけで構成する。

【禁止事項】
- 「ゾクッとした」「背筋が凍った」などの陳腐な表現
- 幽霊が直接的に襲いかかる描写
- オチの説明
- 感情の過剰な描写
- 読み終わるのに3分以上かかること
- 本文内に構成タイトルをつけない

JSON形式のみで出力（解説やタグは一切不要）:
{{"title": "読んだあとに後悔するタイトル（32文字以内）", "content": "Markdown本文全体", "slug": "英数字ハイフンのみ20文字以内"}}"""
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
    
def main():
    posted_file = Path("posted_keywords.json")
    if posted_file.exists():
        posted = json.loads(posted_file.read_text(encoding="utf-8"))
    else:
        posted = []

    remaining = [k for k in KEYWORDS if k not in posted]
    if not remaining:
        print("🔄 全件投稿済み → リセット")
        posted = []
        remaining = KEYWORDS

    keyword = remaining[0]
    print(f"📝 生成中: {keyword}")

    try:
        article = generate_article(keyword)
        article["content"] = insert_affiliate_links(article["content"])
        filename = save_as_jekyll_post(
            article["title"],
            article["content"],
            article["slug"],
            datetime.now()
        )
        posted.append(keyword)
        posted_file.write_text(
            json.dumps(posted, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", f"Add post: {filename}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"✅ 公開完了: {filename}")
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()
