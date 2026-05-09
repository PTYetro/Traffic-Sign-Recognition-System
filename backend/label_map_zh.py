import re


# 第一版：确定性高的精确映射
# 说明：
# 1. 这版优先保证“可读”
# 2. 对于还没有逐个图标精确核对的类别，先做家族级可读映射
EXACT_LABEL_MAP = {
    "pne": "禁止驶入",
    "pg": "减速让行",
    "ps": "停车让行",
    "ip": "人行横道",
    "pn": "停车限制标志",
    "pnl": "停车限制标志（加强）",
}


def _clean_number_text(text: str) -> str:
    """去掉数字字符串末尾多余的小数点，例如 '5.' -> '5'"""
    return text.rstrip(".")


def get_display_name(code: str) -> str:
    """
    将 TT100K 原始类别代码转换为更适合人阅读的显示名称。
    第一版策略：
    1. 规则类精确翻译
    2. 无法精确判断的，先输出“家族 + 编号”
    """
    if not code:
        return ""

    if code in EXACT_LABEL_MAP:
        return EXACT_LABEL_MAP[code]

    # 限速类：pl30 -> 限速30
    m = re.fullmatch(r"pl([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"限速{num}"

    # 最低限速类：il60 -> 最低限速60
    m = re.fullmatch(r"il([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"最低限速{num}"

    # 解除限速类：pr80 -> 解除限速80
    m = re.fullmatch(r"pr([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"解除限速{num}"

    # 限高类：ph3.5 -> 限高3.5米
    m = re.fullmatch(r"ph([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"限高{num}米"

    # 限宽类：pw3 -> 限宽3米
    m = re.fullmatch(r"pw([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"限宽{num}米"

    # 限重类：pm20 -> 限重20吨（第一版先这样处理，后续可细化）
    m = re.fullmatch(r"pm([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"限重{num}吨"

    # 限轴重类：pa10 -> 限轴重10吨（第一版先这样处理，后续可细化）
    m = re.fullmatch(r"pa([0-9.]+)", code)
    if m:
        num = _clean_number_text(m.group(1))
        return f"限轴重{num}吨"

    # 警告标志：w55 -> 警告标志-55
    m = re.fullmatch(r"w([0-9]+)", code)
    if m:
        return f"警告标志-{m.group(1)}"

    # 禁令标志：p26 -> 禁令标志-26
    m = re.fullmatch(r"p([0-9]+)", code)
    if m:
        return f"禁令标志-{m.group(1)}"

    # 指示标志：i10 -> 指示标志-10
    m = re.fullmatch(r"i([0-9]+)", code)
    if m:
        return f"指示标志-{m.group(1)}"

    # 蓝底信息/指示类补充
    if code == "io":
        return "信息标志-io"
    if code == "pi":
        return "禁令标志-pi"
    if code == "po":
        return "禁令标志-po"
    if code == "pb":
        return "禁令标志-pb"
    if code == "pc":
        return "禁令标志-pc"
    if code == "pd":
        return "禁令标志-pd"
    if code == "pe":
        return "禁令标志-pe"

    # 兜底：原样返回
    return code