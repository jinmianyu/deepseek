# -*- coding: utf-8 -*-
"""
============================================================
 PROGRESS.md 生成脚本 —— generate_readme.py
============================================================

【这个脚本是做什么的?】
    读取 progress_data.json 里的所有学习记录,
    自动生成一个排版漂亮的 Markdown 文件:PROGRESS.md

【什么是 Markdown?】
    Markdown 是一种用简单符号来排版的纯文本格式,文件后缀是 .md
    常用符号:
        # 一级标题      ## 二级标题      ### 三级标题
        **加粗**        `行内代码`       - 无序列表项
        | 表格 | 表格 |  --- 分隔线      > 引用
    GitHub 会自动把它渲染成好看的网页,所以 .md 特别适合写 README、进度报告。

【怎么运行?】
    在终端里进入本文件夹,然后输入:
        python generate_readme.py

【和上一个脚本的关系?】
    log_progress.py   负责"收集数据"(写入 json)
    generate_readme.py 负责"展示数据"(读取 json,生成 md)
    这两个脚本共用同一个数据文件,这就是"数据与展示分离"的思想。
============================================================
"""

import json                          # 读写 json 文件
import sys                           # 用来调整运行环境设置(解决 Windows 中文/emoji 崩溃问题)
from datetime import datetime        # 获取当前时间,用于在文件末尾写"最后更新时间"
from pathlib import Path             # 处理文件路径

# 【为什么要加下面这一段?】(Windows 中文用户必看)
# Windows 中文版默认编码是 GBK,不含 emoji。当输出被重定向(管道 | 、日志文件)时,
# Python 用 GBK 编码文字,遇到 emoji 会抛 UnicodeEncodeError 直接崩溃。
# errors="replace" 表示"无法表示的字符用 ? 代替",避免崩溃,中文显示不受影响。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


# ------------------------------------------------------------------
# 第一部分:文件位置
# ------------------------------------------------------------------
# 和 log_progress.py 一样的道理:用脚本自身的位置来定位文件,
# 这样无论你在哪个目录运行脚本,都能找对文件。
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_FILE = SCRIPT_DIR / "progress_data.json"     # 输入:数据来源
OUTPUT_FILE = SCRIPT_DIR / "PROGRESS.md"          # 输出:生成的 Markdown

# 星期几的中文对照表
# datetime.weekday() 返回 0~6,分别代表 周一~周日,用它当下标来查这张表
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


# ------------------------------------------------------------------
# 第二部分:读取数据
# ------------------------------------------------------------------
def load_records(file_path):
    """
    读取学习记录。

    这里和 log_progress.py 里的同名函数作用一样,但处理方式略有不同:
    因为本脚本只是"展示",所以遇到文件不存在时直接给出友好提示并返回空列表,
    不需要再创建文件。
    """
    if not file_path.exists():
        print(f"⚠️  没找到 {file_path.name},请先运行 log_progress.py 记录学习内容。")
        return []

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)          # JSON 文字 → Python 数据
    except json.JSONDecodeError:
        print(f"❌ {file_path.name} 内容不是合法的 JSON,无法生成报告。")
        return []

    # 兼容两种可能的格式:直接是列表,或者是 {"records": [...]}
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return data["records"]

    print("❌ 数据格式不是列表,无法生成报告。")
    return []


# ------------------------------------------------------------------
# 第三部分:统计信息
# ------------------------------------------------------------------
def build_statistics(records):
    """
    根据记录算出一些统计数字,返回一个字典。

    这一步体现了一个常见思路:先把"要展示的东西"算好,
    最后再统一拼成文字,这样逻辑会清楚很多。
    """
    # 取出所有记录的日期(每条记录里的 "date" 字段),组成一个列表
    dates = [r.get("date", "") for r in records if r.get("date")]

    stats = {
        "count": len(records),                                          # 总条数
        "first_date": min(dates) if dates else "-",                     # 最早日期(字符串按字典序比较,日期正好可比)
        "last_date": max(dates) if dates else "-",                      # 最近日期
        "active_days": len(set(dates)) if dates else 0,                 # 有记录的天数(set 会自动去重,所以"不同日期的个数"就是学习天数)
    }
    return stats


# ------------------------------------------------------------------
# 第四部分:生成 Markdown 文本
# ------------------------------------------------------------------
def build_markdown(records):
    """
    把记录拼成 Markdown 文本,返回一个很长的字符串。

    排版结构:
        1. 大标题 + 简介
        2. 学习统计表格
        3. 按日期分组的学习时间线
        4. 页脚(生成时间)
    """
    stats = build_statistics(records)

    # lines 用来装 Markdown 的每一行,最后用 "\n" 把它们连起来
    lines = []

    # ---------- 1. 标题区 ----------
    lines.append("# 🐍 我的 Python 学习旅程")
    lines.append("")
    lines.append("> 记录我从零开始学习 Python 的每一步,由脚本自动生成。")
    lines.append("")
    # HTML 注释在渲染后不可见,用来提醒别人别手动改这个文件
    lines.append("<!-- 本文件由 generate_readme.py 自动生成,请不要手动修改 -->")
    lines.append("")

    # ---------- 2. 统计表格 ----------
    lines.append("## 📊 学习统计")
    lines.append("")
    if stats["count"] == 0:
        lines.append("_还没有任何记录,快去运行 `log_progress.py` 写下第一条吧!_")
    else:
        lines.append("| 统计项 | 数值 |")
        lines.append("| :--- | ---: |")          # :--- 左对齐, ---: 右对齐
        lines.append(f"| 累计记录 | **{stats['count']}** 条 |")
        lines.append(f"| 开始学习 | {stats['first_date']} |")
        lines.append(f"| 最近记录 | {stats['last_date']} |")
        lines.append(f"| 学习天数 | **{stats['active_days']}** 天 |")
    lines.append("")

    # ---------- 3. 按日期分组的时间线 ----------
    lines.append("## 📅 学习时间线")
    lines.append("")

    if not records:
        lines.append("_暂无内容_")
    else:
        # 用一个字典把记录按日期归类
        # 例如 {"2026-10-15": [记录1, 记录2], "2026-10-16": [记录3]}
        grouped = {}
        for record in records:
            date = record.get("date", "未知日期")
            # setdefault 的意思是:如果这个日期还没有列表,就先创建空列表;然后把记录加进去
            grouped.setdefault(date, []).append(record)

        # sorted() 对日期排序,保证时间线从早到晚
        for date in sorted(grouped.keys()):
            # 把 "2026-10-15" 解析成日期对象,以便算出是星期几
            try:
                weekday = WEEKDAY_NAMES[datetime.strptime(date, "%Y-%m-%d").weekday()]
            except ValueError:
                weekday = ""      # 万一日期格式不规范,就留空,不影响整体生成

            lines.append(f"### {date}{f'({weekday})' if weekday else ''}")
            lines.append("")

            # 同一天内的记录,按时间先后排列;没有 time 字段的排在最后
            for record in sorted(grouped[date], key=lambda r: r.get("time", "")):
                time_text = record.get("time", "")
                content = record.get("content", "(内容为空)")
                # `时间` 用行内代码样式显示,内容加粗更醒目
                prefix = f"`{time_text}` " if time_text else ""
                lines.append(f"- {prefix}**{content}**")

            lines.append("")

    # ---------- 4. 页脚 ----------
    lines.append("---")
    lines.append("")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"<sub>最后更新:{generated_at} · 本文件由 `generate_readme.py` 自动生成</sub>")
    lines.append("")

    # join 把列表里所有字符串用换行符连接成一个大字符串
    return "\n".join(lines)


# ------------------------------------------------------------------
# 第五部分:主流程
# ------------------------------------------------------------------
def main():
    print("\n📝 正在生成 PROGRESS.md ...\n")

    records = load_records(DATA_FILE)          # 第 1 步:读数据
    print(f"📊 读到 {len(records)} 条记录")

    markdown = build_markdown(records)         # 第 2 步:拼 Markdown 文本

    # 第 3 步:写入文件
    # encoding="utf-8" 保证中文正常;newline="\n" 保证换行符统一为 LF,
    # 这样推到 GitHub 上显示才不会出现多余空行
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="\n") as f:
        f.write(markdown)

    print(f"✅ 已生成:{OUTPUT_FILE}")
    print(f"   文件大小:{OUTPUT_FILE.stat().st_size} 字节")   # stat().st_size 是文件字节数
    print()
    print("💡 用记事本或 VS Code 打开 PROGRESS.md 就能看到效果;")
    print("   推到 GitHub 后,它会自动渲染成漂亮的网页。")


if __name__ == "__main__":
    main()
