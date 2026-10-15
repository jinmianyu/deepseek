# -*- coding: utf-8 -*-
"""
============================================================
 学习进度记录脚本 —— log_progress.py
============================================================

【这个脚本是做什么的?】
    运行它以后,程序会在终端里问你"今天学了什么?",
    你把学到的内容打进去、按回车,程序就会把这条内容
    存进 progress_data.json 文件里。
    每运行一次,就多存一条记录,旧记录不会被删掉。

【怎么运行?】
    在终端里进入本文件夹(my-python-journey),然后输入:
        python log_progress.py

【为什么要有两个文件?】
    .py  文件 = 程序,负责"逻辑"(怎么问、怎么存)
    .json 文件 = 数据,负责"内容"(存了哪些记录)
    把"程序"和"数据"分开,是编程里非常常见、也非常重要的做法。
    好处是:以后想换一种问法,只改 .py 就行,数据完全不受影响。
============================================================
"""

# ------------------------------------------------------------------
# 第一部分:导入需要的工具(模块)
# ------------------------------------------------------------------
# Python 自带了很多"工具箱",用 import 把它们搬进来才能使用。
import json                     # json 工具箱:负责读写 .json 文件(把数据变成文字、把文字还原成数据)
import sys                      # sys 工具箱:用来调整"运行环境"的设置(下面用它解决 Windows 中文乱码/崩溃问题)
from datetime import datetime   # datetime 工具箱:负责获取"现在是几点几分"
from pathlib import Path        # pathlib 工具箱:负责处理"文件路径"(比老式的 os.path 更直观好用)

# 【为什么要加下面这一段?】(Windows 中文用户必看)
# Windows 中文版的默认编码是 GBK,不含 emoji(比如 🐍)。
# 当我们把输出"重定向"到别的地方(例如管道 | 、日志文件、某些编辑器)时,
# Python 会用 GBK 去编码这些文字,一旦遇到 emoji 就会抛出
# UnicodeEncodeError 让程序直接崩溃。
# errors="replace" 的意思是:遇到无法表示的字符,用 ? 代替,而不是报错。
# 这样既不会崩溃,也不会影响中文的显示。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass          # 极少数旧环境不支持 reconfigure,忽略即可



# ------------------------------------------------------------------
# 第二部分:确定数据文件放在哪里
# ------------------------------------------------------------------
# 【初学者最容易踩的坑】
# 如果直接写字符串 "progress_data.json",这叫"相对路径",
# 它的意思是"相对于你当前所在的文件夹",所以换个目录运行就会找不到文件。
#
# __file__      : 当前这个 .py 文件自己的路径
# .resolve()    : 把路径补成完整的绝对路径,例如 D:\...\my-python-journey\log_progress.py
# .parent       : 取上一级,也就是脚本所在的文件夹 my-python-journey
# / "xxx.json"  : 在这个文件夹里拼出一个文件名
#
# 这样写的好处:不管你在哪个目录运行脚本,数据文件永远和脚本在一起。
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_FILE = SCRIPT_DIR / "progress_data.json"


# ------------------------------------------------------------------
# 第三部分:定义函数
# ------------------------------------------------------------------
# 把"一件事"封装成一个函数,主流程就能写得像目录一样清楚。
def load_records(file_path):
    """
    读取已有的学习记录。

    参数 file_path: 要读取的 json 文件路径(Path 对象)
    返回值         : 一个列表 list,里面每个元素是一条记录(字典 dict)

    【重要思路】JSON 文件不像记事本那样能在末尾"插一行",
    所以想"追加一条记录",标准做法是三步:
        1) 先把文件里原有的内容全部读出来
        2) 在内存里往列表末尾加一条新的
        3) 把整个列表重新写回文件
    下面这几个函数,就是把这个思路拆开来实现。
    """
    # ---- 情况一:文件还不存在(第一次运行) ----
    # Path.exists() 用来判断"这个路径存在吗",返回 True 或 False
    if not file_path.exists():
        print("📄 还没找到 progress_data.json,这是第一次记录,我来帮你新建。")
        return []          # 返回空列表,表示"目前一条记录都没有"

    # ---- 情况二:文件存在,把里面的文字读出来 ----
    # encoding="utf-8" 非常重要!
    # Windows 中文版默认用 GBK 编码,不加这一句,中文存进去可能变乱码。
    try:
        with file_path.open("r", encoding="utf-8") as f:
            # with 语句的好处:用完会自动关闭文件,不用手写 f.close()
            data = json.load(f)     # 把 JSON 文字翻译成 Python 的列表 / 字典
    except json.JSONDecodeError:
        # 如果文件被改坏了(例如手动编辑时少了一个括号),
        # json.load 会报错。我们不想程序直接崩溃,所以:
        # 把损坏的文件改名备份,然后当作"空数据"重新开始。
        backup_path = file_path.with_name("progress_data_broken.json")
        file_path.replace(backup_path)
        print(f"⚠️  数据文件内容损坏,已备份为 {backup_path.name},本次重新开始记录。")
        return []

    # ---- 情况三:确认读出来的内容确实是"列表" ----
    if isinstance(data, list):
        return data

    # 兼容写法:万一以后数据格式改成了 {"records": [...]},这里也能正确取出列表
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return data["records"]

    # 都不是:给出提示并忽略原有内容,避免程序崩溃
    print("⚠️  数据格式不是列表,已忽略原有内容。")
    return []


def save_records(file_path, records):
    """
    把记录列表写回 json 文件。

    注意:这里是"整体重写"文件,但写进去的内容 = 旧记录 + 新记录,
    所以从结果上看,相当于"追加"了一条。

    小知识:newline="\n" 是做什么的?
    Windows 下 Python 默认会把换行符 \n 自动转换成 \r\n(回车+换行),
    这会让文件在不同系统上出现"看不见的差异"(例如 git 显示文件被修改)。
    这里强制写成 \n,可以让 macOS / Linux / Windows 上的结果保持一致,
    推送到 GitHub 后也不会产生多余的空行或改动。
    """
    with file_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(
            records,              # 要写入的数据(Python 列表)
            f,                    # 写到哪个文件
            ensure_ascii=False,   # 关键!False 表示中文直接原样写入,而不是变成 \u5b57 这样的转义码
            indent=2,             # 每层缩进 2 个空格,让文件整齐、方便人直接阅读
        )
        # json.dump 不会自动加末尾换行,这里手动补一个。
        # 文本文件以换行符结尾是通行规范,能让 git 的差异对比更干净。
        f.write("\n")


def ask_content():
    """
    询问用户"今天学了什么",并做最基本的输入检查。

    返回值: 用户输入的内容(字符串);如果用户直接按回车,则返回 None 表示取消。
    """
    print()
    print("=" * 52)
    print("📚 今天学了什么?请输入你的学习内容")
    print("   (输入完成后按回车;什么都不输直接回车 = 取消本次记录)")
    print("=" * 52)

    while True:
        # input() 会把用户输入的文字当作"字符串"返回
        # .strip() 去掉首尾多余的空格和回车,避免只输入空格也被当成有效内容
        content = input("👉 ").strip()

        if content == "":
            return None       # 取消:返回 None(None 在 Python 里表示"什么都没有")

        return content


def main():
    """
    主流程:读旧数据 → 询问内容 → 追加记录 → 写回文件 → 汇报结果。
    把主流程单独写成函数,是为了让代码结构清晰,一眼能看懂顺序。
    """
    print("\n🐍 Python 学习进度记录器\n")

    # 第 1 步:读取已有的记录
    records = load_records(DATA_FILE)
    print(f"📊 目前已有 {len(records)} 条记录")   # len() 用来数"列表里有几个元素"

    # 第 2 步:询问今天学了什么
    content = ask_content()
    if content is None:
        print("\n👋 本次没有记录任何内容,程序结束。")
        return            # return 表示"提前结束函数",后面的代码不执行了

    # 第 3 步:组装一条新记录
    now = datetime.now()  # 拿到当前日期和时间
    new_record = {
        "date": now.strftime("%Y-%m-%d"),   # 日期,例如 2026-10-15
        "time": now.strftime("%H:%M:%S"),   # 时间,例如 21:30:05
        "content": content,                 # 学习内容
    }

    # 第 4 步:追加到列表末尾,并写回文件
    records.append(new_record)              # list.append():在列表末尾加入一个元素 = "追加"
    save_records(DATA_FILE, records)

    # 第 5 步:给用户一个明确的反馈(程序最好"有问有答",体验才好)
    print()
    print("✅ 记录成功!")
    print(f"   内容:{content}")
    print(f"   时间:{new_record['date']} {new_record['time']}")
    print(f"   累计:{len(records)} 条")
    print(f"   文件:{DATA_FILE}")
    print()
    print("💡 下一步:运行  python generate_readme.py  就能生成漂亮的 PROGRESS.md")


# ------------------------------------------------------------------
# 第四部分:程序入口
# ------------------------------------------------------------------
# 这一行的意思是:只有当"直接运行本文件"时,才执行 main()。
# 如果别的脚本用 import 引用了本文件,main() 就不会自动执行,避免误触发。
if __name__ == "__main__":
    main()
