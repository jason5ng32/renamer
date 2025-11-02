#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正则模式：逐项提问，完全自定义批量重命名
"""
import sys
import re
from pathlib import Path
from utils import (
    ask, ask_yes_no, ask_choice, dotify_if_no_dot,
    check_conflicts_or_exit, preview_and_confirm, two_phase_rename,
    check_matches_and_retry, ask_numbering_config, format_number,
    console, Colors
)
from rich.text import Text

def count_capture_groups(match_src: str, flags: str) -> int:
    """计算所有正则表达式的总捕获组数量"""
    if not match_src:
        return 0
    
    patterns = [s.strip() for s in match_src.split(",") if s.strip()]
    total_groups = 0
    
    fl = 0
    f = flags.lower() if flags else ""
    if "i" in f:
        fl |= re.IGNORECASE
    if "m" in f:
        fl |= re.MULTILINE
    if "s" in f:
        fl |= re.DOTALL
    
    for pattern in patterns:
        try:
            compiled = re.compile(pattern, fl)
            total_groups += compiled.groups
        except re.error:
            pass
    
    return total_groups

def count_replace_references(replace_expr: str) -> int:
    """计算替换表达式中的捕获组引用数量（$1, $2, ...）"""
    # 匹配 $1, $2, ... $99 等格式
    matches = re.findall(r'\$(\d+)', replace_expr)
    if not matches:
        return 0
    
    # 返回引用的最大编号
    max_ref = max(int(m) for m in matches)
    return max_ref

def flow_normal_mode():
    console.print(f"\n[{Colors.MODE_TITLE_BLUE}]== 正则模式 ==[/]")
    
    dir_str = ask("请输入目录路径", default=".")
    dir_path = Path(dir_str).expanduser().resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        console.print(f"[{Colors.ERROR}]目录不存在：[/]{dir_path}")
        sys.exit(1)

    # 扩展名输入（必填项，不允许空值）
    while True:
        ext = ask("请输入扩展名（不要带点）").lstrip(".").lower()
        
        # 检查扩展名匹配的文件数量
        count, should_retry = check_matches_and_retry(dir_path, ext, match_src=None, flags="i")
        if not should_retry:
            break

    # 匹配项输入
    while True:
        console.print(f"\n[{Colors.BOLD}]匹配项说明：[/]")
        # 使用 Text 对象来避免数字和特殊字符被意外着色
        console.print(Text("- 留空（直接回车）= 将不查找匹配项，直接采用后续规则进行批量重命名", style=Colors.SECONDARY))
        console.print(Text("- 自定义正则 = 将匹配文件名中的特定内容，并通过捕获组提取内容，用于新文件名", style=Colors.SECONDARY))
        console.print(Text("-- 支持多个捕获组，在替换表达式中可用 $1, $2, $3... 引用", style=Colors.SECONDARY))
        console.print(Text("-- 示例：([A-Z]+)(\\d+) 有两个捕获组，可用 $1 和 $2 引用", style=Colors.SECONDARY))
        
        match_src = ask("请输入匹配项（留空表示按序号重命名）", allow_empty=True)
        
        # 留空就是空匹配
        if match_src == "":
            match_src = ""  # 空匹配（按序号）
            replace_expr = None  # 空匹配不需要替换表达式
            total_capture_groups = 0
            flags = "i"  # 空匹配不需要 flags，但为了兼容性设置
            break  # 空匹配直接退出循环
        else:
            # 自定义正则：验证格式
            try:
                # 验证正则表达式格式
                patterns = [s.strip() for s in match_src.split(",") if s.strip()]
                for pattern in patterns:
                    re.compile(pattern)  # 尝试编译以验证格式
            except re.error as e:
                console.print(f"[{Colors.ERROR}]正则表达式格式错误：{e}[/]")
                continue
            
            # 正则模式下不使用任何默认 flags，完全遵循用户输入的正则表达式
            flags = ""
            
            # 先检查匹配项后的文件数量（在询问替换表达式之前）
            count, should_retry = check_matches_and_retry(dir_path, ext, match_src, flags, prompt_context="")
            if should_retry:
                continue  # 重新输入匹配项
            
            # 只有找到匹配项才继续处理
            # 计算捕获组数量
            total_capture_groups = count_capture_groups(match_src, flags)
            
            if total_capture_groups == 0:
                console.print(f"[{Colors.WARNING}]警告：正则表达式中没有捕获组，无法提取内容进行替换。[/]")
                if not ask_yes_no("是否继续？（将只匹配但不替换）", default=False):
                    continue
                replace_expr = None
            else:
                # 如果有捕获组，需要替换表达式（无论是单捕获组还是多捕获组）
                console.print(f"\n[{Colors.BOLD}]检测到 {total_capture_groups} 个捕获组。[/]")
                # 使用 Text 对象来避免数字和特殊字符被意外着色
                console.print(Text("请在替换表达式中使用 $1, $2, $3... 来引用捕获组。", style=Colors.SECONDARY))
                console.print(Text("示例：如果匹配 ([A-Z]+)(\\d+)，可用 '$1_$2' 或 '前缀$2' 等", style=Colors.SECONDARY))
                
                while True:
                    replace_expr = ask("请输入替换表达式（使用 $1, $2... 引用捕获组）", allow_empty=False)
                    
                    # 验证替换表达式中的引用数量
                    max_ref = count_replace_references(replace_expr)
                    if max_ref > total_capture_groups:
                        console.print(f"[{Colors.ERROR}]错误：替换表达式中引用了 ${max_ref}，但只有 {total_capture_groups} 个捕获组。[/]")
                        continue
                    if max_ref == 0 and total_capture_groups > 0:
                        console.print(f"[{Colors.WARNING}]警告：替换表达式中没有使用任何捕获组引用（$1, $2...）。[/]")
                        if not ask_yes_no("是否继续？", default=True):
                            continue
                    break
            
            # 匹配项验证完成，退出循环
            break
    
    # 前缀和后缀输入
    # 如果使用了替换表达式（有捕获组），则不需要前缀和后缀（这些都在替换表达式中了）
    # 如果为空匹配，需要前缀和序号
    # 如果无捕获组，需要前缀（虽然这种情况很少）
    to_prefix = None
    suffix = None
    
    if match_src == "":
        # 空匹配模式：使用前缀+序号
        to_prefix = ask("请输入前缀（将用于生成文件名，如：file_）")
        to_prefix = dotify_if_no_dot(to_prefix)
    elif total_capture_groups > 0:
        # 使用替换表达式模式：前缀和后缀都包含在替换表达式中，不需要额外询问
        pass
    else:
        # 无捕获组：需要前缀（虽然这种情况应该很少）
        to_prefix = ask("请输入前缀（将用于生成文件名）")
        to_prefix = dotify_if_no_dot(to_prefix)
    
    # 排序方式（仅空匹配模式需要）
    sort_key = "name"
    if match_src == "":
        sort_key = ask_choice("编号排序方式：", 
                             ["按文件名排序（name）", "按修改时间排序（mtime）"])
        if sort_key.startswith("按文件名排序"):
            sort_key = "name"
        else:
            sort_key = "mtime"
    
    # 起始编号和数字位数（仅空匹配模式需要）
    start = 0
    padding_width = 0
    if match_src == "":
        start, padding_width = ask_numbering_config()
    
    # 扩展名替换
    new_ext = ext
    if ask_yes_no("是否替换扩展名？", default=False):
        new_ext = ask("请输入新扩展名（不要带点）", default=ext).lstrip(".").lower()
    
    # 生成计划（需要扩展 build_plans 函数支持新的参数）
    # 这里暂时先调用，后续需要修改 build_plans
    plans = build_plans_normal_mode(dir_path, ext, match_src, flags, to_prefix, suffix, 
                                    start, sort_key, padding_width, replace_expr, 
                                    total_capture_groups, new_ext)
    
    if not plans:
        console.print(f"[{Colors.WARNING}]未找到可重命名的文件（检查目录/扩展名/匹配条件）。[/]")
        sys.exit(0)

    plans = check_conflicts_or_exit(dir_path, plans, start, padding_width)
    if preview_and_confirm(dir_path, plans):
        two_phase_rename(dir_path, plans)
        console.print(f"[{Colors.SUCCESS_BOLD}]✅ 重命名完成。[/]")
    else:
        console.print(f"[{Colors.SECONDARY}]已取消。[/]")

def build_plans_normal_mode(dir_path: Path, ext: str, match_src: str, flags: str,
                            to_prefix: str, suffix: str, start: int, sort_key: str, 
                            padding_width: int, replace_expr: str, total_capture_groups: int,
                            new_ext: str):
    """正则模式的计划生成函数"""
    from utils import is_file, compile_matchers, pick_parts
    
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
            new_name = f"{new_base}.{new_ext}"
            if p.name != new_name:
                plans.append((p.name, new_name))
            n += 1
    elif total_capture_groups > 0 and replace_expr:
        # 多捕获组模式：使用替换表达式
        matchers = compile_matchers(match_src, flags)
        for p in files:
            base = p.stem
            # 查找匹配
            matched = False
            match_obj = None
            for reobj in matchers:
                m = reobj.search(base)
                if m:
                    matched = True
                    match_obj = m
                    break
            
            if not matched:
                continue
            
            # 使用替换表达式生成新文件名
            # 保持捕获组的原始格式（不转换为整数，以保留前导零等）
            new_base = replace_expr
            # 从后往前替换，避免 $1 被替换后影响 $10 等
            for i in range(match_obj.lastindex or 0, 0, -1):
                try:
                    group_value = match_obj.group(i)
                    # 保持原始格式，不进行数字转换（这样 "01" 会保持为 "01"）
                    # 如果需要补零，可以通过替换表达式和 format_number 来处理
                    new_base = new_base.replace(f"${i}", group_value)
                except (IndexError, AttributeError):
                    pass
            
            new_name = f"{new_base}.{new_ext}"
            if p.name != new_name:
                plans.append((p.name, new_name))
    else:
        # 无捕获组模式：使用前缀（这种情况很少，因为没有捕获组就无法提取内容）
        # 实际上这个分支可能不会被执行，因为前面已经要求有捕获组
        # 但保留作为容错处理
        matchers = compile_matchers(match_src, flags)
        for p in files:
            base = p.stem
            # 检查是否能匹配（但不提取捕获组）
            matched = False
            for reobj in matchers:
                if reobj.search(base):
                    matched = True
                    break
            
            if not matched:
                continue
            
            # 无捕获组：只能使用前缀
            if to_prefix:
                new_base = to_prefix
            else:
                new_base = base  # 如果没有前缀，保持原样
            new_name = f"{new_base}.{new_ext}"
            if p.name != new_name:
                plans.append((p.name, new_name))

    return plans
