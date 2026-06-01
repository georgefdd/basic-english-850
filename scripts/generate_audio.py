#!/usr/bin/env python3
"""Basic English 850 — 音频生成脚本

使用 edge-tts 为指定周的词+例句生成学习音频。

功能：
  week     — 生成某周的词+例句音频
  words    — 生成指定词列表的音频
  listen   — 生成听写练习音频（只读词，不读释义）

用法：
  python3 generate_audio.py week --week 1 --voice en-US-JennyNeural
  python3 generate_audio.py words --list "come,get,give,go" --voice en-US-GuyNeural
  python3 generate_audio.py listen --week 2 --output listen-w2.mp3

依赖：pip install edge-tts
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("❌ 请先安装 edge-tts: pip install edge-tts")
    sys.exit(1)

# 默认输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'BasicEnglish', 'audio')

# 各周词表（简化版，与references词表对应）
WEEK_WORDS = {
    1: {  # Operations
        "verbs": ["come","get","give","go","keep","let","make","put","seem","take","be","do","have","say","see","send","may","will"],
        "pronouns": ["I","he","you","who"],
        "determiners": ["a","the","all","any","every","no","other","some","such","that","this"],
        "prepositions": ["about","across","after","against","among","at","before","between","by","down","from","in","off","on","over","through","to","under","up","with"],
        "conjunctions": ["and","because","but","or","if","though","as","for","of","till"],
        "adverbs": ["how","when","where","why","again","ever","far","forward","here","near","now","out","still","then","there","together","well","almost","enough","even","little","much","not","only","quite","so","very","tomorrow","yesterday"],
        "directions": ["north","south","east","west"],
        "other": ["please","yes"]
    },
}

# 例句（与references/example-sentences.md对应）
WORD_SENTENCES = {
    "come": "Come here, please.",
    "get": "I get up early.",
    "give": "Give me the book.",
    "go": "I go to work by train.",
    "keep": "Keep the door open.",
    "let": "Let me see.",
    "make": "Make a decision.",
    "put": "Put it on the table.",
    "seem": "He seems happy.",
    "take": "Take this to him.",
    "be": "I am a teacher.",
    "do": "Do your work now.",
    "have": "I have a new hat.",
    "say": "He says yes.",
    "see": "I see the sea.",
    "send": "Send me a letter.",
    "may": "May I come in?",
    "will": "I will go tomorrow.",
    "about": "Tell me about it.",
    "across": "Go across the bridge.",
    "after": "After dinner, we go.",
    "against": "I am against the war.",
    "among": "Among the trees.",
    "at": "At the station.",
    "before": "Before you go.",
    "between": "Between you and me.",
    "by": "By the door.",
    "down": "Come down.",
    "from": "From here to there.",
    "in": "In the room.",
    "off": "Get off the train.",
    "on": "On the table.",
    "over": "Over the wall.",
    "through": "Come through the door.",
    "to": "Go to the house.",
    "under": "Under the tree.",
    "up": "Get up.",
    "with": "With my friend.",
    "and": "You and I.",
    "because": "Because it is late.",
    "but": "Good but expensive.",
    "or": "Tea or coffee?",
    "if": "If you go, I will go.",
    "though": "Though he is ill, he works.",
}

VOICE_MAP = {
    "female-us": "en-US-JennyNeural",
    "male-us": "en-US-GuyNeural",
    "female-uk": "en-GB-SoniaNeural",
    "male-uk": "en-GB-RyanNeural",
}


async def generate_audio_file(text: str, voice: str, output_path: str, rate: str = "+0%"):
    """用 edge-tts 生成单段音频"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


async def generate_week_audio(week: int, voice: str, output: str, rate: str = "+0%"):
    """生成某周的完整学习音频"""
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    if week not in WEEK_WORDS:
        # For weeks not explicitly defined, use flat word list
        print(f"⚠️  Week {week} 词表未内置，请使用 --words 模式指定词列表")
        return

    week_data = WEEK_WORDS[week]
    all_words = []
    for category, words in week_data.items():
        all_words.extend(words)

    print(f"🎤 生成 Week {week} 音频 ({len(all_words)} 词)...")
    print(f"   语音: {voice}")
    print(f"   输出: {output}")

    # Build SSML-like text with pauses
    segments = []
    for word in all_words:
        # Word (slow)
        segments.append(word)
        # Pause for repetition (using silence marker)
        segments.append("... ")
        # Example sentence
        if word.lower() in WORD_SENTENCES:
            segments.append(WORD_SENTENCES[word.lower()])
        segments.append("... ")

    full_text = " ".join(segments)

    # Generate at slower rate for learning
    await generate_audio_file(full_text, voice, output, rate="-10%")

    file_size = os.path.getsize(output) if os.path.exists(output) else 0
    print(f"✅ 音频已生成: {output} ({file_size / 1024:.0f} KB)")


async def generate_words_audio(words: list, voice: str, output: str, rate: str = "+0%"):
    """生成指定词列表的音频"""
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    print(f"🎤 生成 {len(words)} 词的音频...")

    segments = []
    for word in words:
        segments.append(word)
        segments.append("... ")
        if word.lower() in WORD_SENTENCES:
            segments.append(WORD_SENTENCES[word.lower()])
        segments.append("... ")

    full_text = " ".join(segments)
    await generate_audio_file(full_text, voice, output, rate="-10%")

    file_size = os.path.getsize(output) if os.path.exists(output) else 0
    print(f"✅ 音频已生成: {output} ({file_size / 1024:.0f} KB)")


async def generate_listen_audio(week: int, voice: str, output: str):
    """生成听写练习音频（只读英文词，不读释义，留空白时间写）"""
    if week not in WEEK_WORDS:
        print(f"⚠️  Week {week} 词表未内置")
        return

    week_data = WEEK_WORDS[week]
    all_words = []
    for category, words in week_data.items():
        all_words.extend(words)

    print(f"🎧 生成 Week {week} 听写音频 ({len(all_words)} 词)...")

    segments = []
    for word in all_words:
        segments.append(word)
        # Longer pause for writing
        segments.append("...... ")

    full_text = " ".join(segments)
    await generate_audio_file(full_text, voice, output, rate="+0%")

    file_size = os.path.getsize(output) if os.path.exists(output) else 0
    print(f"✅ 听写音频已生成: {output} ({file_size / 1024:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Basic English 850 音频生成")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # week
    week_parser = subparsers.add_parser("week", help="生成某周学习音频")
    week_parser.add_argument("--week", type=int, required=True, help="周次(1-6)")
    week_parser.add_argument("--voice", default="en-US-JennyNeural", help="语音")
    week_parser.add_argument("--output", default=None, help="输出文件路径")
    week_parser.add_argument("--rate", default="-10%", help="语速调整")

    # words
    words_parser = subparsers.add_parser("words", help="生成指定词列表音频")
    words_parser.add_argument("--list", required=True, help="词列表(逗号分隔)")
    words_parser.add_argument("--voice", default="en-US-JennyNeural", help="语音")
    words_parser.add_argument("--output", default="custom-words.mp3", help="输出文件")
    words_parser.add_argument("--rate", default="-10%", help="语速调整")

    # listen
    listen_parser = subparsers.add_parser("listen", help="生成听写练习音频")
    listen_parser.add_argument("--week", type=int, required=True, help="周次")
    listen_parser.add_argument("--voice", default="en-US-JennyNeural", help="语音")
    listen_parser.add_argument("--output", default=None, help="输出文件")

    args = parser.parse_args()

    if args.command == "week":
        output = args.output or os.path.join(OUTPUT_DIR, f"week{args.week}.mp3")
        asyncio.run(generate_week_audio(args.week, args.voice, output, args.rate))

    elif args.command == "words":
        words = [w.strip() for w in args.list.split(",")]
        asyncio.run(generate_words_audio(words, args.voice, args.output, args.rate))

    elif args.command == "listen":
        output = args.output or os.path.join(OUTPUT_DIR, f"listen-week{args.week}.mp3")
        asyncio.run(generate_listen_audio(args.week, args.voice, output))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
