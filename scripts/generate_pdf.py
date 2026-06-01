#!/usr/bin/env python3
"""Basic English 850 — 学习内容PDF生成脚本

将每日学习内容排版为可打印的A4 PDF，方便纸质学习。

功能：
  morning   — 生成早晨学习PDF（词卡+听写+阅读）
  evening   — 生成晚间练习PDF（回顾+口语提示+写作区）
  review    — 生成复习PDF（薄弱词+5秒回忆+场景串联）
  test      — 生成自测PDF（听写/选择/翻译/造句）

用法：
  python3 generate_pdf.py morning --week 1 --day 2 --output ./day2-morning.pdf
  python3 generate_pdf.py evening --week 1 --day 2 --output ./day2-evening.pdf

依赖：pip install reportlab
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── 字体注册 ──
FONT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')

# 注册中文字体（按优先级尝试）
CN_FONT_NAME = "CJKFont"
CN_FONT_CANDIDATES = [
    ("SimHei", "/usr/share/fonts/truetype/simhei.ttf"),           # 经典黑体
    ("IPAPGothic", "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"),  # IPA P Gothic（含CJK）
    ("IPAGothic", "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"),    # IPA Gothic
]

cn_font_registered = False
for name, path in CN_FONT_CANDIDATES:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            CN_FONT_NAME = name
            cn_font_registered = True
            break
        except Exception:
            continue

if not cn_font_registered:
    CN_FONT_NAME = "Helvetica"
    print("⚠️  未找到中文字体，中文将以Helvetica渲染")

# ── 颜色 ──
C_PRIMARY = HexColor("#1a5276")      # 深蓝标题
C_ACCENT = HexColor("#2e86c1")       # 蓝色强调
C_LIGHT_BG = HexColor("#eaf2f8")     # 浅蓝背景
C_HEADER_BG = HexColor("#2e86c1")    # 表头背景
C_HEADER_FG = white                  # 表头文字
C_BORDER = HexColor("#aed6f1")       # 边框色
C_GREY = HexColor("#7f8c8d")         # 灰色注释
C_DICTATION_BG = HexColor("#fef9e7") # 听写区淡黄背景
C_WRITING_BG = HexColor("#f9f9f9")   # 写作区灰色背景

# ── 样式 ──
def get_styles():
    s = getSampleStyleSheet()
    font = CN_FONT_NAME
    styles = {
        'title': ParagraphStyle('Title', fontName=font, fontSize=22, leading=28,
                                textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=4*mm),
        'subtitle': ParagraphStyle('Subtitle', fontName=font, fontSize=12, leading=16,
                                   textColor=C_GREY, alignment=TA_CENTER, spaceAfter=6*mm),
        'section': ParagraphStyle('Section', fontName=font, fontSize=14, leading=20,
                                  textColor=C_PRIMARY, spaceAfter=3*mm, spaceBefore=6*mm),
        'word_cell': ParagraphStyle('WordCell', fontName='Helvetica-Bold', fontSize=12, leading=16,
                                    textColor=C_PRIMARY),
        'phonetic': ParagraphStyle('Phonetic', fontName='Helvetica', fontSize=9, leading=12,
                                   textColor=C_GREY),
        'meaning': ParagraphStyle('Meaning', fontName=font, fontSize=11, leading=15),
        'example': ParagraphStyle('Example', fontName='Helvetica', fontSize=10, leading=14,
                                  textColor=HexColor("#34495e")),
        'example_cn': ParagraphStyle('ExampleCN', fontName=font, fontSize=9, leading=12,
                                     textColor=C_GREY),
        'reading': ParagraphStyle('Reading', fontName='Helvetica', fontSize=12, leading=18,
                                  textColor=HexColor("#2c3e50")),
        'reading_cn': ParagraphStyle('ReadingCN', fontName=font, fontSize=10, leading=15,
                                     textColor=C_GREY),
        'hint': ParagraphStyle('Hint', fontName=font, fontSize=10, leading=14,
                               textColor=C_GREY),
        'dictation_num': ParagraphStyle('DictNum', fontName='Helvetica-Bold', fontSize=12,
                                        textColor=C_ACCENT),
        'dictation_line': ParagraphStyle('DictLine', fontName=font, fontSize=10,
                                         textColor=C_GREY),
        'footer': ParagraphStyle('Footer', fontName=font, fontSize=8, leading=10,
                                 textColor=C_GREY, alignment=TA_CENTER),
    }
    return styles


# ── 页脚 ──
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(CN_FONT_NAME, 8)
    canvas.setFillColor(C_GREY)
    canvas.drawCentredString(A4[0] / 2, 12 * mm,
                              f"Basic English 850 — Week {doc.week} Day {doc.day}  |  Page {doc.page}")
    canvas.restoreState()


# ── 早晨学习PDF ──
def generate_morning_pdf(week, day, words_data, output_path):
    """
    words_data: list of dicts with keys: word, phonetic, meaning, example, example_cn
    """
    styles = get_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm, leftMargin=15*mm, rightMargin=15*mm
    )
    doc.week = week
    doc.day = day

    elements = []

    # ── 标题 ──
    elements.append(Paragraph(f"🌅 Basic English 850 — Morning", styles['title']))
    elements.append(Paragraph(f"Week {week} Day {day}  |  {datetime.now().strftime('%Y-%m-%d')}", styles['subtitle']))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    elements.append(Spacer(1, 4*mm))

    # ── 词卡表格 ──
    elements.append(Paragraph("📚 今日新词", styles['section']))

    # 分组：每页最多20个词
    chunk_size = 20
    for chunk_start in range(0, len(words_data), chunk_size):
        chunk = words_data[chunk_start:chunk_start + chunk_size]

        table_data = [
            [Paragraph('<b>#</b>', styles['word_cell']),
             Paragraph('<b>Word</b>', styles['word_cell']),
             Paragraph('<b>Phonetic</b>', styles['phonetic']),
             Paragraph('<b>Meaning</b>', styles['meaning']),
             Paragraph('<b>Example</b>', styles['example'])]
        ]

        for i, w in enumerate(chunk, 1):
            row = [
                Paragraph(f'<b>{i}</b>', styles['dictation_num']),
                Paragraph(f'<b>{w["word"]}</b>', styles['word_cell']),
                Paragraph(w.get('phonetic', ''), styles['phonetic']),
                Paragraph(w.get('meaning', ''), styles['meaning']),
                Paragraph(w.get('example', ''), styles['example']),
            ]
            table_data.append(row)

        col_widths = [8*mm, 25*mm, 28*mm, 28*mm, 99*mm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_HEADER_FG),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), CN_FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, C_LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4*mm))

        if chunk_start + chunk_size < len(words_data):
            elements.append(PageBreak())

    # ── 听写区 ──
    elements.append(Paragraph("✍️ 轻量听写（昨日词回顾）", styles['section']))
    elements.append(Spacer(1, 2*mm))

    dict_rows = []
    for i in range(1, 6):
        dict_rows.append([
            Paragraph(f'<b>{i}.</b>', styles['dictation_num']),
            Paragraph('_____________', styles['dictation_line']),
            Paragraph('→', styles['dictation_line']),
            Paragraph('_____________', styles['dictation_line']),
        ])

    dict_table = Table(dict_rows, colWidths=[10*mm, 55*mm, 10*mm, 55*mm])
    dict_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), C_DICTATION_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor("#f0e68c")),
    ]))
    elements.append(dict_table)
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("提示：听到词后写下英文和中文释义", styles['hint']))
    elements.append(Spacer(1, 4*mm))

    # ── 阅读训练 ──
    elements.append(Paragraph("📖 阅读训练", styles['section']))
    elements.append(Spacer(1, 2*mm))

    reading_sentences = [
        ("A cat is on the table.", "一只猫在桌子上。"),
        ("All the children came after school.", "所有孩子放学后都来了。"),
        ("I have some books, but no time to read.", "我有一些书，但没有时间读。"),
        ("Every person in this room is against the idea.", "这个房间里的每个人都反对这个想法。"),
        ("The shop is between the bank and the park.", "商店在银行和公园之间。"),
    ]

    for i, (en, cn) in enumerate(reading_sentences, 1):
        elements.append(Paragraph(f'<b>{i}.</b>  {en}', styles['reading']))
        elements.append(Paragraph(f'     {cn}', styles['reading_cn']))
        elements.append(Spacer(1, 2*mm))

    # 构建
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"✅ 早晨学习PDF已生成: {output_path} ({os.path.getsize(output_path)/1024:.0f} KB)")


# ── 晚间练习PDF ──
def generate_evening_pdf(week, day, words_data, output_path):
    """words_data: 今日词的快速回顾列表"""
    styles = get_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm, leftMargin=15*mm, rightMargin=15*mm
    )
    doc.week = week
    doc.day = day

    elements = []

    # ── 标题 ──
    elements.append(Paragraph("🌙 Basic English 850 — Evening", styles['title']))
    elements.append(Paragraph(f"Week {week} Day {day}  |  {datetime.now().strftime('%Y-%m-%d')}", styles['subtitle']))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    elements.append(Spacer(1, 4*mm))

    # ── 快速回顾 ──
    elements.append(Paragraph("🔄 快速回顾（只看英文，写出释义）", styles['section']))

    review_data = [[Paragraph('<b>#</b>', styles['word_cell']),
                     Paragraph('<b>Word</b>', styles['word_cell']),
                     Paragraph('<b>Meaning</b>', styles['meaning'])]]
    for i, w in enumerate(words_data, 1):
        review_data.append([
            Paragraph(f'<b>{i}</b>', styles['dictation_num']),
            Paragraph(f'<b>{w["word"]}</b>', styles['word_cell']),
            Paragraph('_____________', styles['dictation_line']),
        ])

    review_table = Table(review_data, colWidths=[10*mm, 35*mm, 80*mm])
    review_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_HEADER_FG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, C_LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(review_table)
    elements.append(Spacer(1, 6*mm))

    # ── 口语练习区 ──
    elements.append(Paragraph("🗣️ 口语练习", styles['section']))
    elements.append(Paragraph("用指定5个词各造1句（口头表达，写下来备查）", styles['hint']))
    elements.append(Spacer(1, 2*mm))

    for i in range(1, 6):
        elements.append(Paragraph(f'<b>{i}.</b>  Word: ___________  Sentence: ___________________________________', styles['reading']))
        elements.append(Spacer(1, 3*mm))

    elements.append(Spacer(1, 4*mm))

    # ── 写作区 ──
    elements.append(Paragraph("✏️ Basic English 日记", styles['section']))
    week_prompts = {
        1: "5句简单陈述（I go to work. I see my friend.）",
        2: "5句+物品描述（I put my cup on the table.）",
        3: "5句+形容词描述（The hot sweet tea is good.）",
        4: "5-8句+观点表达（In my opinion, ... is important.）",
        5: "5-8句+观点表达",
        6: "10句自由写作",
    }
    prompt = week_prompts.get(week, "5句日记")
    elements.append(Paragraph(f"提示：{prompt}", styles['hint']))
    elements.append(Paragraph("规则：只用850词，不查词典，不会表达就换个说法", styles['hint']))
    elements.append(Spacer(1, 3*mm))

    # 写作横线区
    for i in range(1, 11):
        elements.append(Paragraph(
            f'<b>{i}.</b> _______________________________________________________________',
            styles['reading']
        ))
        elements.append(Spacer(1, 3*mm))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"✅ 晚间练习PDF已生成: {output_path} ({os.path.getsize(output_path)/1024:.0f} KB)")


# ── 自测PDF ──
def generate_test_pdf(week, day, test_type, questions, output_path):
    """
    test_type: dictation / choice / translation / sentence
    questions: list of dicts depending on type
    """
    styles = get_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm, leftMargin=15*mm, rightMargin=15*mm
    )
    doc.week = week
    doc.day = day

    elements = []

    type_names = {
        'dictation': '📝 听写测试',
        'choice': '✅ 选择题',
        'translation': '🔄 翻译测试',
        'sentence': '✏️ 造句测试',
    }

    elements.append(Paragraph(f"📝 Basic English 850 — Test", styles['title']))
    elements.append(Paragraph(
        f"Week {week}  |  {type_names.get(test_type, test_type)}  |  {datetime.now().strftime('%Y-%m-%d')}",
        styles['subtitle']
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    elements.append(Spacer(1, 4*mm))

    if test_type == 'dictation':
        elements.append(Paragraph("听写测试：听到词后写下英文和中文释义", styles['section']))
        for i in range(1, 11):
            elements.append(Paragraph(
                f'<b>{i}.</b>  English: ________________  Chinese: ________________',
                styles['reading']
            ))
            elements.append(Spacer(1, 4*mm))

    elif test_type == 'choice':
        elements.append(Paragraph("选择题：选择正确的中文释义", styles['section']))
        for i, q in enumerate(questions, 1):
            elements.append(Paragraph(f'<b>{i}. {q["word"]}</b>', styles['reading']))
            for opt in q['options']:
                elements.append(Paragraph(f'   □ {opt}', styles['reading']))
            elements.append(Spacer(1, 3*mm))

    elif test_type == 'translation':
        elements.append(Paragraph("中译英（5句）", styles['section']))
        for i, q in enumerate(questions[:5], 1):
            elements.append(Paragraph(f'<b>{i}.</b> {q["cn"]}', styles['reading']))
            elements.append(Paragraph(f'   _______________________________________', styles['reading']))
            elements.append(Spacer(1, 3*mm))
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph("英译中（5句）", styles['section']))
        for i, q in enumerate(questions[5:], 1):
            elements.append(Paragraph(f'<b>{i}.</b> {q["en"]}', styles['reading']))
            elements.append(Paragraph(f'   _______________________________________', styles['reading']))
            elements.append(Spacer(1, 3*mm))

    elif test_type == 'sentence':
        elements.append(Paragraph("造句测试：用每个词造1句", styles['section']))
        for i, w in enumerate(questions, 1):
            elements.append(Paragraph(
                f'<b>{i}. {w}</b>  ________________________________________________',
                styles['reading']
            ))
            elements.append(Spacer(1, 5*mm))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"✅ 自测PDF已生成: {output_path} ({os.path.getsize(output_path)/1024:.0f} KB)")


# ── 复习PDF ──
def generate_review_pdf(week, day, weak_words, output_path):
    """weak_words: list of dicts {word, meaning}"""
    styles = get_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm, leftMargin=15*mm, rightMargin=15*mm
    )
    doc.week = week
    doc.day = day

    elements = []

    elements.append(Paragraph("📖 Basic English 850 — Review", styles['title']))
    elements.append(Paragraph(f"Week {week}  |  {datetime.now().strftime('%Y-%m-%d')}", styles['subtitle']))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    elements.append(Spacer(1, 4*mm))

    # 5秒回忆
    elements.append(Paragraph("⚡ 5秒回忆测试（看到词→5秒内写出释义+1个句子）", styles['section']))
    for i, w in enumerate(weak_words, 1):
        elements.append(Paragraph(
            f'<b>{i}. {w["word"]}</b>  Meaning: ____________  Sentence: ________________________________',
            styles['reading']
        ))
        elements.append(Spacer(1, 4*mm))

    # 场景串联区
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("🔗 场景串联（用5个词编一段话）", styles['section']))
    elements.append(Paragraph("词: __________  __________  __________  __________  __________", styles['reading']))
    elements.append(Spacer(1, 3*mm))
    for i in range(1, 6):
        elements.append(Paragraph(f'   _______________________________________________________________', styles['reading']))
        elements.append(Spacer(1, 3*mm))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"✅ 复习PDF已生成: {output_path} ({os.path.getsize(output_path)/1024:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Basic English 850 — 学习PDF生成")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # morning
    m = subparsers.add_parser("morning", help="早晨学习PDF")
    m.add_argument("--week", type=int, required=True)
    m.add_argument("--day", type=int, required=True)
    m.add_argument("--output", default=None, help="输出路径")

    # evening
    e = subparsers.add_parser("evening", help="晚间练习PDF")
    e.add_argument("--week", type=int, required=True)
    e.add_argument("--day", type=int, required=True)
    e.add_argument("--output", default=None, help="输出路径")

    # test
    t = subparsers.add_parser("test", help="自测PDF")
    t.add_argument("--week", type=int, required=True)
    t.add_argument("--type", required=True, choices=["dictation", "choice", "translation", "sentence"])
    t.add_argument("--output", default=None, help="输出路径")

    # review
    r = subparsers.add_parser("review", help="复习PDF")
    r.add_argument("--week", type=int, required=True)
    r.add_argument("--output", default=None, help="输出路径")

    args = parser.parse_args()

    # 默认输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'BasicEnglish', 'pdf')
    os.makedirs(output_dir, exist_ok=True)

    # 读取进度
    progress_path = os.path.join(os.path.dirname(__file__), '..', 'progress.json')
    if os.path.exists(progress_path):
        with open(progress_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    else:
        progress = {}

    # 示例词数据（实际应由调用方传入或从词表读取）
    sample_words = [
        {"word": "a", "phonetic": "/ə/", "meaning": "一个", "example": "A dog is a good pet."},
        {"word": "the", "phonetic": "/ðə/", "meaning": "这个/那个", "example": "The book is on the table."},
        {"word": "all", "phonetic": "/ɔːl/", "meaning": "所有", "example": "All the boys are here."},
    ]

    if args.command == "morning":
        output = args.output or os.path.join(output_dir, f"week{args.week}-day{args.day}-morning.pdf")
        generate_morning_pdf(args.week, args.day, sample_words, output)
    elif args.command == "evening":
        output = args.output or os.path.join(output_dir, f"week{args.week}-day{args.day}-evening.pdf")
        generate_evening_pdf(args.week, args.day, sample_words, output)
    elif args.command == "test":
        output = args.output or os.path.join(output_dir, f"week{args.week}-test-{args.type}.pdf")
        generate_test_pdf(args.week, 0, args.type, [], output)
    elif args.command == "review":
        output = args.output or os.path.join(output_dir, f"week{args.week}-review.pdf")
        generate_review_pdf(args.week, 0, [], output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
