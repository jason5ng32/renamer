#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数模块
包含所有通用的工具函数、颜色处理、交互、文件操作等
"""
import os
import re
import sys
import time
from pathlib import Path

# 改善终端输入体验（支持方向键、历史记录等）
# 注意：使用 Rich Console 的 input() 方法可以正确处理带颜色的 prompt，
# 避免删除键删除 prompt 的问题，所以不再需要单独配置 readline
try:
    import readline
except ImportError:
    pass

# --------------------- 颜色工具（使用 Rich）--------------------
from rich.console import Console
from rich.text import Text

# 创建全局 Console 实例
console = Console()
# 创建 stderr 的 Console 实例用于错误输出
console_err = Console(file=sys.stderr)

# 语义化的样式常量（基于 Rich）
class Colors:
    """语义化样式映射（基于 Rich）"""
    # 基础样式
    RESET = ''
    BOLD = 'bold'
    DIM = 'dim'
    
    # 语义化样式
    PROMPT = 'cyan'  # 用户输入提示
    INFO = 'cyan'  # 信息显示
    WARNING = 'yellow'  # 警告信息
    ERROR = 'red'  # 错误信息
    SUCCESS = 'green'  # 成功信息
    
    # 组合样式
    TITLE = 'bold cyan'  # 标题
    MODE_TITLE_MAGENTA = 'bold magenta'  # 模式标题（影视模式）
    MODE_TITLE_BLUE = 'bold blue'  # 模式标题（正则模式）
    ERROR_BOLD = 'bold red'  # 严重错误
    SUCCESS_BOLD = 'bold green'  # 成功完成
    HIGHLIGHT = 'yellow'  # 高亮显示
    SECONDARY = 'dim'  # 次要/辅助信息
    ARROW = 'cyan'  # 箭头指示

def colorize(text: str, color: str = Colors.RESET) -> str:
    """
    为文本添加颜色（兼容函数，返回带 Rich 标记的字符串）
    注意：返回的是 Rich 标记字符串，需要使用 console.print() 才能显示颜色
    如果直接使用 print()，会显示标记字符
    """
    if not color or color == Colors.RESET:
        return text
    
    # 处理组合样式（如 BOLD + CYAN）
    if '+' in color:
        styles = [s.strip() for s in color.split('+') if s.strip()]
        style_str = ' '.join(styles)
    else:
        style_str = color
    
    # 返回 Rich 标记字符串
    return f"[{style_str}]{text}[/]"

# --------------------- 通用工具 ---------------------
def dotify_if_no_dot(s: str) -> str:
    """若字符串完全不含点，则把空格（含中文全角空格）替换为点；否则原样返回。"""
    if s is None:
        return s
    if '.' in s:
        return s.strip()
    out = re.sub(r'[\s\u3000]+', '.', s.strip())
    out = re.sub(r'\.+', '.', out)
    return out

def is_file(p: Path) -> bool:
    try:
        return p.is_file()
    except Exception:
        return False

# --------------------- 交互函数 ---------------------
def ask(prompt: str, default: str = None, allow_empty: bool = False) -> str:
    """通用输入：支持默认值和是否允许空值。
    将 prompt 和用户输入分开两行显示，避免删除键删除 prompt。
    """
    while True:
        # 先显示 prompt（换行，这样不会被用户输入影响）
        if default is not None:
            console.print(f"[{Colors.PROMPT}]{prompt}[/] [[{Colors.SECONDARY}]{default}[/]]")
        else:
            console.print(f"[{Colors.PROMPT}]{prompt}[/]")
        
        # 在单独的一行显示输入提示符，用户在这一行输入
        console.print(f"[{Colors.SECONDARY}]> [/]", end="")
        sys.stdout.flush()
        val = input().strip()
        
        if val == "" and default is not None:
            return default
        if val == "" and allow_empty:
            return ""
        if val == "" and not allow_empty:
            console.print(f"[{Colors.WARNING}]请输入内容。[/]")
            continue
        return val

def ask_yes_no(prompt: str, default: bool = False) -> bool:
    """Y/N 选择。
    将 prompt 和用户输入分开两行显示，避免删除键删除 prompt。
    """
    d_text = f"[{Colors.SUCCESS}]Y/n[/]" if default else f"[{Colors.SECONDARY}]y/N[/]"
    # 先显示 prompt（换行）
    console.print(f"[{Colors.PROMPT}]{prompt}[/] ({d_text})")
    # 在单独的一行显示输入提示符
    console.print(f"[{Colors.SECONDARY}]> [/]", end="")
    sys.stdout.flush()
    s = input().strip().lower()
    if s == "" and default is not None:
        return default
    return s in ("y", "yes")

def ask_choice(prompt: str, options) -> str:
    """
    单选菜单。options: list[str]。返回选择值。
    """
    console.print(f"[{Colors.TITLE}]{prompt}[/]")
    for i, opt in enumerate(options, 1):
        # 使用 Text 对象来避免选项文本被解析为 Rich 标记
        option_text = Text()
        option_text.append(f"  ", style=Colors.RESET)
        option_text.append(str(i), style=Colors.HIGHLIGHT)
        option_text.append(f") {opt}", style=Colors.RESET)
        console.print(option_text)
    while True:
        # 先显示 prompt（换行）
        console.print(f"[{Colors.PROMPT}]请输入序号: [/]")
        # 在单独的一行显示输入提示符
        console.print(f"[{Colors.SECONDARY}]> [/]", end="")
        sys.stdout.flush()
        idx = input().strip()
        if not idx.isdigit():
            console.print(f"[{Colors.WARNING}]请输入数字序号。[/]")
            continue
        idx = int(idx)
        if 1 <= idx <= len(options):
            return options[idx-1]
        console.print(f"[{Colors.WARNING}]无效的序号，请重试。[/]")

# --------------------- 正则匹配工具 ---------------------
def compile_matchers(match_src: str, flags: str):
    """
    将匹配模式转换为正则列表：
    - match_src 为 None：未设置（不应在此处使用）
    - match_src 为空字符串：返回 [] 表示"空匹配（编号模式）"
    - 否则，按逗号分隔多个模式
    flags: "i", "im", "is" 等
    """
    if match_src is None:
        return []
    
    if match_src == "":
        return []
    
    patterns = [s.strip() for s in match_src.split(",") if s.strip()]

    fl = 0
    f = flags.lower() if flags else ""
    if "i" in f:
        fl |= re.IGNORECASE
    if "m" in f:
        fl |= re.MULTILINE
    if "s" in f:
        fl |= re.DOTALL

    return [re.compile(p, fl) for p in patterns]

def pick_parts(basename_no_ext: str, matchers, preserve_format: bool = False):
    """
    在不含扩展名的文件名中查找匹配：
    返回 (pre, ep, tail)；ep 为第一个捕获组，tail 为匹配后的剩余。
    
    preserve_format: 如果为 True，保持捕获组的原始格式（如 "01"）；否则转换为整数（如 "1"）
    """
    for reobj in matchers:
        m = reobj.search(basename_no_ext)
        if not m:
            continue
        # 检查是否有捕获组
        if m.lastindex is None or m.lastindex == 0:
            # 没有捕获组，跳过这个匹配
            continue
        try:
            if preserve_format:
                # 保持原始格式（用于普通模式）
                ep = m.group(1)
            else:
                # 转换为整数（用于影视模式，保持向后兼容）
                ep = str(int(m.group(1)))
        except (IndexError, ValueError):
            # 捕获组不存在或无法转换为整数，跳过
            continue
        start, end = m.span()
        pre = basename_no_ext[:start]
        tail = basename_no_ext[end:]
        return pre, ep, tail
    return None

# --------------------- 编号配置工具 ---------------------
def format_number(num: int, padding_width: int = 0) -> str:
    """格式化数字，应用补零规则"""
    if padding_width > 0:
        return str(num).zfill(padding_width)
    return str(num)

def ask_numbering_config(prompt_prefix: str = "") -> tuple[int, int]:
    """
    询问用户数字编号配置（起始编号和补零位数）
    返回 (start, padding_width)
    """
    prefix = f"{prompt_prefix} " if prompt_prefix else ""
    
    # 询问起始编号（支持0）
    while True:
        start_str = ask(f"{prefix}起始编号（支持0）", default="0")
        try:
            start = int(start_str)
            if start < 0:
                console.print(f"[{Colors.WARNING}]起始编号不能为负数。[/]")
                continue
            break
        except ValueError:
            console.print(f"[{Colors.WARNING}]请输入有效的数字。[/]")
            continue
    
    # 询问数字位数（用于补零）
    while True:
        padding_str = ask(f"{prefix}数字位数（用于补零，如设为2则显示01、02，设为0则不补零）", default="0")
        try:
            padding_width = int(padding_str)
            if padding_width < 0:
                console.print(f"[{Colors.WARNING}]数字位数不能为负数。[/]")
                continue
            break
        except ValueError:
            console.print(f"[{Colors.WARNING}]请输入有效的数字。[/]")
            continue
    
    return start, padding_width

# --------------------- 文件操作 ---------------------
def preview_and_confirm(dir_path: Path, plans):
    """预览重命名计划并确认"""
    console.print(f"\n[{Colors.BOLD}]目录：[/][{Colors.INFO}]{dir_path}[/]")
    console.print(f"[{Colors.BOLD}]重命名计划[/]（共 [{Colors.HIGHLIGHT}]{len(plans)}[/] 个）：\n")
    for src, dst in plans:
        # 使用 Text 对象来避免文件名被解析为 Rich 标记，防止数字被意外着色
        src_text = Text(src, style=Colors.SECONDARY)
        dst_text = Text(dst, style=Colors.SUCCESS)
        arrow_text = Text("->", style=Colors.ARROW)
        console.print(src_text)
        console.print(f"  ", end="")
        console.print(arrow_text, end=" ")
        console.print(dst_text)
        console.print()  # 空行
    return ask_yes_no("确认执行以上重命名吗？", default=False)

def two_phase_rename(dir_path: Path, plans):
    """两阶段安全重命名：避免链式覆盖。"""
    temp_tag = f".__tmp__{int(time.time()*1000)}__"
    try:
        for src, _ in plans:
            a = dir_path / src
            a_tmp = dir_path / f"{src}{temp_tag}"
            os.replace(a, a_tmp)
        for src, dst in plans:
            a_tmp = dir_path / f"{src}{temp_tag}"
            b = dir_path / dst
            os.replace(a_tmp, b)
    except Exception as e:
        console_err.print(f"[{Colors.ERROR_BOLD}]重命名失败：[/]{e}")
        console_err.print(f'[{Colors.WARNING}]注意：若中止，目录中可能留下包含 "__tmp__" 的临时文件，请手动清理。[/]')
        sys.exit(3)

# --------------------- 匹配统计 ---------------------
def count_matches(dir_path: Path, ext: str, match_src: str = None, flags: str = "i"):
    """
    统计目录中匹配的文件数量。
    - ext: 扩展名（不含点）
    - match_src: 匹配模式，None 表示需要匹配模式，"" 表示空匹配（按序号）
    - flags: 正则flags
    返回匹配的文件数量
    """
    files = [p for p in dir_path.iterdir() if is_file(p) and p.suffix.lower() == f".{ext.lower()}"]
    
    if match_src is None:
        # 尚未设置匹配模式，返回符合扩展名的文件数
        return len(files)
    
    if match_src == "":
        # 空匹配：所有符合扩展名的文件都算匹配
        return len(files)
    
    # 有匹配模式：需要检查文件名是否能匹配
    matchers = compile_matchers(match_src, flags)
    count = 0
    for p in files:
        base = p.stem
        parts = pick_parts(base, matchers)
        if parts:
            count += 1
    return count

def check_matches_and_retry(dir_path: Path, ext: str, match_src: str = None, flags: str = "i", prompt_context: str = ""):
    """
    检查匹配数量，如果为0则询问是否重来。
    返回 (count, should_retry)
    """
    count = count_matches(dir_path, ext, match_src, flags)
    context_msg = f" [{prompt_context}]" if prompt_context else ""
    if count > 0:
        console.print(f"[{Colors.WARNING}]找到 {count} 个匹配的 {ext} 文件{context_msg}[/]")
    else:
        console.print(f"[{Colors.ERROR}]找到 {count} 个匹配的 {ext} 文件{context_msg}[/]")
    
    if count == 0:
        if ask_yes_no("未找到匹配的文件，是否重新配置？", default=True):
            return (0, True)
        else:
            console.print(f"[{Colors.SECONDARY}]已取消操作。[/]")
            sys.exit(0)
    return (count, False)

# --------------------- 计划生成 ---------------------
def build_plans(dir_path: Path, ext: str, match_src: str, flags: str,
                to_prefix: str, suffix: str, start: int, sort_key: str, padding_width: int = 0):
    """生成 (src, dst) 列表。
    padding_width: 数字位数，用于补零。0 表示不补零。
    """
    files = [p for p in dir_path.iterdir() if is_file(p) and p.suffix.lower() == f".{ext.lower()}"]

    plans = []
    if match_src == "":
        # 空匹配：按排序编号
        if sort_key == "mtime":
            files.sort(key=lambda p: p.stat().st_mtime)
        else:
            files.sort(key=lambda p: p.name)
        n = start
        for p in files:
            # 格式化数字位数
            n_str = format_number(n, padding_width)
            new_base = f"{to_prefix}{n_str}"
            new_name = f"{new_base}{p.suffix}"
            if p.name != new_name:
                plans.append((p.name, new_name))
            n += 1
    else:
        matchers = compile_matchers(match_src, flags)
        for p in files:
            base = p.stem
            parts = pick_parts(base, matchers)
            if not parts:
                continue
            _, ep, tail = parts

            left = to_prefix[:-1] if to_prefix.endswith(".") else to_prefix
            
            # 格式化集数位数
            try:
                ep_num = int(ep)
                ep_formatted = format_number(ep_num, padding_width)
            except ValueError:
                # 如果无法转换为整数，使用原始值
                ep_formatted = ep
            
            ep_seg = f"E{ep_formatted}"

            if suffix is not None:
                mid = f".{suffix}" if suffix else ""
            else:
                t = re.sub(r'^\.+', '', tail)
                t = re.sub(r'\.+$', '', t)
                mid = f".{t}" if t else ""

            new_base = f"{left}.{ep_seg}{mid}"
            new_name = f"{new_base}{p.suffix}"
            if p.name != new_name:
                plans.append((p.name, new_name))

    return plans

# --------------------- 冲突处理 ---------------------
def check_conflicts(dir_path: Path, plans):
    """检查冲突，返回 (has_conflict, conflicts)
    conflicts: 冲突列表，每个冲突包含 type ('duplicate' 或 'exists') 和其他信息
    """
    existing = {p.name for p in dir_path.iterdir()}
    tgt = {}
    conflicts = []
    
    for src, dst in plans:
        if dst in tgt:
            # 多个源文件重命名为同一目标
            conflicts.append({
                'type': 'duplicate',
                'dst': dst,
                'sources': [tgt[dst], src]
            })
        else:
            tgt[dst] = src
        
        if (dst in existing) and (dst not in {s for s, _ in plans}):
            # 目标名已存在
            conflicts.append({
                'type': 'exists',
                'dst': dst,
                'source': src
            })
    
    return len(conflicts) > 0, conflicts

def resolve_conflicts_with_suffix(dir_path: Path, plans, conflicts, start: int = 0, padding_width: int = 0):
    """为冲突的文件添加数字后缀来解决冲突
    start: 数字后缀的起始编号（第一个冲突文件也使用这个编号）
    padding_width: 数字后缀的补零位数
    注意：和视频模式一致，第一个文件也添加起始编号，且不使用下划线
    """
    # 获取目录中已存在的文件名（排除即将被重命名的源文件）
    existing = {p.name for p in dir_path.iterdir()}
    sources = {src for src, _ in plans}
    # 只考虑非源文件的已存在文件
    existing_excluding_sources = existing - sources
    
    # 先统计所有计划中的目标名，找出重复的目标名
    dst_to_sources = {}
    for src, dst in plans:
        if dst not in dst_to_sources:
            dst_to_sources[dst] = []
        dst_to_sources[dst].append(src)
    
    # 跟踪已使用的名称（包括已存在的文件和已解决的名称）
    used_names = set(existing_excluding_sources)
    resolved_plans = []
    dst_count = {}  # 统计每个目标名出现的次数
    
    for src, dst in plans:
        # 检查是否有多个文件使用相同的目标名，或者目标名已存在
        has_duplicate = len(dst_to_sources.get(dst, [])) > 1
        exists_in_dir = dst in existing_excluding_sources
        
        if has_duplicate or exists_in_dir:
            # 需要添加编号（第一个文件也添加起始编号）
            base_name, ext = os.path.splitext(dst)
            if dst not in dst_count:
                dst_count[dst] = start  # 第一个冲突使用起始编号
            else:
                dst_count[dst] += 1  # 后续冲突递增
            
            counter = dst_count[dst]
            suffix_str = format_number(counter, padding_width)
            # 不使用下划线，直接拼接（和视频模式一致）
            new_dst = f"{base_name}{suffix_str}{ext}"
            
            # 确保新名字不冲突（如果已存在，继续递增）
            while new_dst in used_names:
                counter += 1
                suffix_str = format_number(counter, padding_width)
                new_dst = f"{base_name}{suffix_str}{ext}"
            
            dst_count[dst] = counter
            used_names.add(new_dst)
            resolved_plans.append((src, new_dst))
        else:
            # 目标名唯一且不存在，直接使用
            used_names.add(dst)
            resolved_plans.append((src, dst))
    
    return resolved_plans

def check_conflicts_or_exit(dir_path: Path, plans, start: int = 0, padding_width: int = 0, auto_resolve: bool = False):
    """检查冲突，如果启用自动解决则添加数字后缀
    start: 数字后缀的起始编号
    padding_width: 数字后缀的补零位数
    """
    has_conflict, conflicts = check_conflicts(dir_path, plans)
    
    if not has_conflict:
        return plans
    
    # 显示冲突信息（最多显示2个示例）
    display_count = min(len(conflicts), 2)
    for i, conflict in enumerate(conflicts[:display_count]):
        # 使用 Text 对象来避免文件名被解析为 Rich 标记
        if conflict['type'] == 'duplicate':
            conflict_msg = Text()
            conflict_msg.append("冲突：多个源文件会重命名为相同目标名 -> ", style=Colors.ERROR)
            conflict_msg.append(conflict['dst'], style=Colors.HIGHLIGHT)
            console_err.print(conflict_msg)
        else:
            conflict_msg = Text()
            conflict_msg.append("冲突：目标名已存在 -> ", style=Colors.ERROR)
            conflict_msg.append(conflict['dst'], style=Colors.HIGHLIGHT)
            console_err.print(conflict_msg)
    
    if len(conflicts) > 2:
        remaining = len(conflicts) - 2
        console_err.print(f"[{Colors.SECONDARY}]... 还有 {remaining} 个冲突[/]")
    
    if auto_resolve:
        # 自动解决：添加数字后缀（需要考虑已存在的文件）
        resolved_plans = resolve_conflicts_with_suffix(dir_path, plans, conflicts, start, padding_width)
        console.print(f"\n[{Colors.SUCCESS}]已自动为冲突的文件添加数字后缀。[/]")
        return resolved_plans
    
    # 询问用户是否自动解决
    console_err.print(f"\n[{Colors.ERROR_BOLD}]⚠️ 检测到冲突。[/]")
    
    if ask_yes_no("是否自动为冲突的文件添加数字后缀来解决冲突？", default=True):
        # 询问编号配置（和视频模式一致）
        console.print(f"\n[{Colors.BOLD}]请设置冲突解决时的数字编号配置：[/]")
        conflict_start, conflict_padding = ask_numbering_config("冲突后缀")
        
        resolved_plans = resolve_conflicts_with_suffix(dir_path, plans, conflicts, conflict_start, conflict_padding)
        console.print(f"[{Colors.SUCCESS}]已自动为冲突的文件添加数字后缀。[/]")
        return resolved_plans
    else:
        console_err.print(f"[{Colors.ERROR_BOLD}]请处理冲突后重试。[/]")
        sys.exit(2)

