#!/usr/bin/env python3
"""Basic English 850 — 进度追踪脚本

功能：
  init      — 初始化进度文件
  show      — 显示当前进度
  update    — 更新词状态（mark/weak/master）
  log       — 记录当日学习日志
  weak      — 列出薄弱词
  export    — 导出进度报告

用法：
  python3 track_progress.py init
  python3 track_progress.py show
  python3 track_progress.py update --word "through" --status weak
  python3 track_progress.py update --word "through" --status mastered
  python3 track_progress.py log --mode morning --new 20
  python3 track_progress.py weak
  python3 track_progress.py export --output progress-report.md
"""

import json
import argparse
import os
from datetime import datetime, date
from pathlib import Path

PROGRESS_FILE = os.path.join(os.path.dirname(__file__), '..', 'progress.json')

# 全量850词列表
ALL_WORDS = [
    # Operations - 100
    "a","able","about","account","acid","across","act","addition","adjustment","advertisement",
    "after","again","against","agreement","air","all","almost","among","amount","amusement",
    "and","angle","angry","animal","answer","ant","any","apparatus","apple","approval",
    "arch","argument","arm","army","art","as","asleep","at","attack","attempt","attention",
    "attraction","authority","automatic","awake",
    "baby","back","bad","bag","balance","ball","band","base","basin","basket",
    "bath","be","beautiful","because","bed","bee","before","behavior","belief","bell",
    "bent","berry","between","bird","birth","bit","bite","bitter","black","blade",
    "blood","blow","blue","board","boat","body","boiling","bone","book","boot",
    "bottle","box","boy","brain","brake","branch","brass","bread","breath","brick",
    "bridge","bright","broken","brother","brown","brush","bucket","building","bulb","burn",
    "burst","business","but","butter","button","by",
    "cake","camera","canvas","card","care","carriage","cart","cat","cause","certain",
    "chain","chalk","chance","change","cheap","cheese","chemical","chest","chief","chin",
    "church","circle","clean","clear","clock","cloth","cloud","coal","coat","cold",
    "collar","color","comb","come","comfort","committee","common","company","comparison","complete",
    "competition","complex","condition","connection","conscious","control","cook","copper","copy","cord",
    "cork","cotton","cough","country","cover","cow","crack","credit","crime","cruel",
    "crush","cry","cup","current","curtain","curve","cushion","cut",
    "damage","danger","dark","daughter","day","dead","dear","death","debt","decision",
    "deep","degree","delicate","dependent","design","desire","destruction","detail","development","different",
    "digestion","direction","dirty","discovery","discussion","disease","disgust","distance","distribution","division",
    "do","dog","doubt","down","drain","drawer","dress","drink","driving","drop",
    "dry","dust",
    "ear","early","earth","east","edge","education","effect","egg","elastic","electric",
    "end","engine","enough","equal","error","even","event","ever","every","example",
    "exchange","existence","expansion","experience","expert","eye",
    "face","fact","fall","false","family","far","farm","fat","father","fear",
    "feather","feeble","feeling","female","fertile","fiction","field","fight","finger","fire",
    "first","fish","fixed","flag","flame","flat","flight","floor","flower","fly",
    "fold","food","foolish","foot","for","force","fork","form","forward","fowl",
    "frame","free","frequent","friend","from","front","fruit","full","future",
    "empty","garden","general","get","girl","give","glass","glove","go","goat","gold",
    "good","government","grain","grass","great","green","grey","grip","group","growth",
    "guide","gun",
    "hair","hammer","hand","hanging","happy","harbor","hard","harmony","hat","hate",
    "have","he","head","healthy","hearing","heart","heat","help","here","high",
    "heavy","history","hole","hollow","hook","hope","horn","horse","hospital","hot","hour","house",
    "how","humor",
    "I","ice","idea","if","ill","important","impulse","in","increase","industry",
    "ink","insect","instrument","insurance","interest","invention","iron","island",
    "jelly","jewel","join","journey","judge","jump",
    "keep","kettle","key","kick","kind","kiss","knee","knife","knot","knowledge",
    "land","language","last","late","laugh","law","lead","leaf","learning","leather",
    "left","leg","let","letter","level","library","lift","light","like","limit",
    "line","linen","lip","liquid","list","little","living","lock","long","look",
    "loose","loss","loud","love","low",
    "machine","make","male","man","manager","map","mark","market","married","match",
    "material","mass","may","meal","measure","meat","medical","meeting","memory","metal",
    "middle","military","milk","mind","mine","minute","mist","mixed","money","monkey",
    "month","moon","morning","mother","motion","mountain","mouth","move","much","muscle",
    "music",
    "nail","name","narrow","nation","natural","near","necessary","neck","need","needle",
    "nerve","net","new","news","night","no","noise","normal","north","nose",
    "not","note","now","number","nut",
    "observation","of","off","offer","office","oil","old","on","only","open",
    "operation","opinion","opposite","or","orange","order","organization","ornament","other","out",
    "oven","over","owner",
    "page","pain","paint","paper","parallel","parcel","part","past","paste","payment",
    "peace","pen","pencil","person","physical","picture","pig","pin","pipe","place",
    "plane","plant","plate","play","please","pleasure","plough","pocket","point","poison",
    "polish","political","poor","porter","position","possible","pot","potato","powder","power",
    "present","price","print","prison","private","probable","process","produce","profit","property",
    "prose","protest","public","pull","pump","punishment","purpose","push","put",
    "quality","question","quick","quiet","quite",
    "rail","rain","range","rat","rate","ray","reaction","reading","ready","reason",
    "receipt","record","red","regret","regular","relation","religion","representative","request","respect",
    "responsible","rest","reward","rhythm","rice","right","ring","river","road","rod",
    "roll","roof","room","root","rough","round","rub","rule","run",
    "sad","safe","sail","salt","same","sand","say","scale","school","science",
    "scissors","screw","sea","seat","second","secret","secretary","see","seed","selection",
    "self","send","seem","sense","separate","serious","servant","sex","shade","shake",
    "shallow","shame","sharp","sheep","shelf","ship","shirt","shock","shoe","short","shut",
    "side","sign","silk","silver","simple","sister","size","skin","skirt","sky",
    "sleep","slip","slope","slow","small","smash","smell","smile","smoke","smooth",
    "snake","sneeze","snow","so","soap","society","sock","soft","solid","some",
    "son","song","sort","sound","south","soup","space","spade","special","sponge",
    "spoon","spring","square","stamp","stage","star","start","statement","station","steam",
    "stem","steel","step","stick","sticky","still","stitch","stocking","stomach","stone",
    "stop","store","story","strange","street","stretch","stiff","straight","strong","structure",
    "substance","such","sudden","sugar","suggestion","summer","sun","support","surprise","sweet",
    "swim","system",
    "table","tail","take","talk","tall","taste","tax","teaching","tendency","test",
    "than","that","the","then","theory","there","thick","thin","thing","this",
    "though","thought","thread","throat","through","thumb","thunder","ticket","tight","till",
    "time","tin","tired","to","toe","together","tomorrow","tongue","tooth","top",
    "touch","town","trade","train","transport","tray","tree","trick","trouble","trousers",
    "true","turn","twist",
    "umbrella","under","unit","up","use",
    "value","verse","very","vessel","view","violent","voice",
    "waiting","walk","wall","war","warm","wash","waste","watch","water","wave",
    "wax","way","weather","week","weight","well","west","wet","wheel","when",
    "where","while","whip","whistle","white","who","why","wide","will","wind",
    "window","wine","wing","winter","wire","wise","with","woman","wood","wool",
    "word","work","worm","wound","writing","wrong",
    "year","yellow","yes","yesterday","you","young"
]


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_progress(data):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_init(args):
    """初始化进度文件"""
    data = {
        "current_week": 1,
        "current_day": 1,
        "start_date": date.today().isoformat(),
        "words": {},
        "daily_log": [],
        "stats": {
            "total_mastered": 0,
            "total_review": 0,
            "total_weak": 0,
            "total_unseen": len(ALL_WORDS),
            "streak_days": 0
        }
    }
    for w in ALL_WORDS:
        data["words"][w] = {
            "status": "unseen",
            "first_seen": None,
            "last_review": None,
            "error_count": 0
        }
    save_progress(data)
    print(f"✅ 进度文件已初始化，共 {len(ALL_WORDS)} 个词")
    print(f"📅 开始日期: {data['start_date']}")


def cmd_show(args):
    """显示当前进度"""
    data = load_progress()
    if not data:
        print("❌ 进度文件不存在，请先运行 init")
        return

    mastered = sum(1 for w in data["words"].values() if w["status"] == "mastered")
    review = sum(1 for w in data["words"].values() if w["status"] == "review")
    weak = sum(1 for w in data["words"].values() if w["status"] == "weak")
    practiced = sum(1 for w in data["words"].values() if w["status"] == "practiced")
    seen = sum(1 for w in data["words"].values() if w["status"] == "seen")
    unseen = sum(1 for w in data["words"].values() if w["status"] == "unseen")
    total_seen = len(ALL_WORDS) - unseen
    pct = total_seen / len(ALL_WORDS) * 100

    # Progress bar
    filled = int(pct / 5)
    bar = "█" * filled + "░" * (20 - filled)

    # Recent daily log
    recent = data["daily_log"][-7:] if data["daily_log"] else []

    print("📊 Basic English 850 学习进度")
    print("=" * 40)
    print(f"当前阶段: Week {data['current_week']} / Day {data['current_day']}")
    print(f"开始日期: {data['start_date']}")
    print(f"连续学习: {data['stats']['streak_days']} 天")
    print()
    print(f"已学词数: {total_seen} / {len(ALL_WORDS)} ({pct:.1f}%)")
    print(f"进度: [{bar}] {pct:.1f}%")
    print()
    print(f"✅ 已掌握: {mastered}")
    print(f"🔄 需复习: {review}")
    print(f"📝 已练习: {practiced}")
    print(f"👀 已接触: {seen}")
    print(f"⚠️  薄弱词: {weak}")
    print(f"⬜ 未学习: {unseen}")

    if recent:
        print()
        print("📅 最近学习记录:")
        for log in recent:
            print(f"  {log['date']} | {log['mode']:8s} | 新词: {log.get('new_words', 0)} | 复习: {log.get('review_words', 0)}")


def cmd_update(args):
    """更新词状态"""
    data = load_progress()
    if not data:
        print("❌ 进度文件不存在，请先运行 init")
        return

    word = args.word.lower().strip()
    status = args.status

    if word not in data["words"]:
        print(f"❌ 词 '{word}' 不在850词表中")
        return

    old_status = data["words"][word]["status"]
    today = date.today().isoformat()

    data["words"][word]["status"] = status
    data["words"][word]["last_review"] = today

    if old_status == "unseen" and data["words"][word]["first_seen"] is None:
        data["words"][word]["first_seen"] = today

    if status == "weak":
        data["words"][word]["error_count"] += 1

    # Recalculate stats
    recalc_stats(data)
    save_progress(data)
    print(f"✅ '{word}' 状态: {old_status} → {status}")


def cmd_log(args):
    """记录当日学习日志"""
    data = load_progress()
    if not data:
        print("❌ 进度文件不存在，请先运行 init")
        return

    today = date.today().isoformat()
    entry = {
        "date": today,
        "mode": args.mode,
        "new_words": args.new or 0,
        "review_words": args.review or 0
    }
    data["daily_log"].append(entry)

    # Update streak
    if data["daily_log"]:
        dates = sorted(set(log["date"] for log in data["daily_log"]))
        streak = 1
        for i in range(len(dates) - 1, 0, -1):
            d1 = date.fromisoformat(dates[i])
            d2 = date.fromisoformat(dates[i-1])
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        data["stats"]["streak_days"] = streak

    save_progress(data)
    print(f"✅ 已记录 {args.mode} session: 新词{args.new or 0}, 复习{args.review or 0}")


def cmd_weak(args):
    """列出薄弱词"""
    data = load_progress()
    if not data:
        print("❌ 进度文件不存在，请先运行 init")
        return

    weak_words = [(w, info) for w, info in data["words"].items()
                  if info["status"] in ("weak", "review")]

    if not weak_words:
        print("✅ 没有薄弱词，表现不错！")
        return

    # Sort by error_count desc
    weak_words.sort(key=lambda x: x[1]["error_count"], reverse=True)

    print(f"⚠️  薄弱词列表 ({len(weak_words)} 个):")
    print("-" * 40)
    for i, (w, info) in enumerate(weak_words[:20], 1):
        print(f"  {i:2d}. {w:20s} 状态:{info['status']:8s} 错误:{info['error_count']}次")
    if len(weak_words) > 20:
        print(f"  ... 还有 {len(weak_words) - 20} 个")


def cmd_export(args):
    """导出进度报告"""
    data = load_progress()
    if not data:
        print("❌ 进度文件不存在，请先运行 init")
        return

    mastered = sum(1 for w in data["words"].values() if w["status"] == "mastered")
    review = sum(1 for w in data["words"].values() if w["status"] == "review")
    weak = sum(1 for w in data["words"].values() if w["status"] == "weak")
    unseen = sum(1 for w in data["words"].values() if w["status"] == "unseen")
    total_seen = len(ALL_WORDS) - unseen
    pct = total_seen / len(ALL_WORDS) * 100

    weak_list = [(w, info) for w, info in data["words"].items()
                 if info["status"] in ("weak", "review")]
    weak_list.sort(key=lambda x: x[1]["error_count"], reverse=True)

    report = f"""# Basic English 850 学习进度报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 总体进度

- 当前阶段: Week {data['current_week']} / Day {data['current_day']}
- 开始日期: {data['start_date']}
- 连续学习: {data['stats']['streak_days']} 天
- 已学词数: {total_seen} / {len(ALL_WORDS)} ({pct:.1f}%)
- 已掌握: {mastered}
- 需复习: {review}
- 薄弱词: {weak}
- 未学习: {unseen}

## 薄弱词 TOP 20

"""
    for i, (w, info) in enumerate(weak_list[:20], 1):
        report += f"{i}. **{w}** — 状态: {info['status']}, 错误: {info['error_count']}次\n"

    output = args.output or "progress-report.md"
    with open(output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 报告已导出到 {output}")


def recalc_stats(data):
    mastered = sum(1 for w in data["words"].values() if w["status"] == "mastered")
    review = sum(1 for w in data["words"].values() if w["status"] == "review")
    weak = sum(1 for w in data["words"].values() if w["status"] == "weak")
    unseen = sum(1 for w in data["words"].values() if w["status"] == "unseen")
    data["stats"]["total_mastered"] = mastered
    data["stats"]["total_review"] = review
    data["stats"]["total_weak"] = weak
    data["stats"]["total_unseen"] = unseen


def main():
    parser = argparse.ArgumentParser(description="Basic English 850 进度追踪")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init
    subparsers.add_parser("init", help="初始化进度文件")

    # show
    subparsers.add_parser("show", help="显示当前进度")

    # update
    update_parser = subparsers.add_parser("update", help="更新词状态")
    update_parser.add_argument("--word", required=True, help="要更新的词")
    update_parser.add_argument("--status", required=True,
                               choices=["seen", "practiced", "review", "mastered", "weak"],
                               help="新状态")

    # log
    log_parser = subparsers.add_parser("log", help="记录学习日志")
    log_parser.add_argument("--mode", required=True, choices=["morning", "evening", "review", "test"],
                            help="学习模式")
    log_parser.add_argument("--new", type=int, help="新学词数")
    log_parser.add_argument("--review", type=int, help="复习词数")

    # weak
    subparsers.add_parser("weak", help="列出薄弱词")

    # export
    export_parser = subparsers.add_parser("export", help="导出进度报告")
    export_parser.add_argument("--output", default="progress-report.md", help="输出文件")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "weak":
        cmd_weak(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
