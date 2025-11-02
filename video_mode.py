#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影视模式：提供常用扩展名/匹配写法的快捷选项
"""
import sys
import re
from pathlib import Path
from utils import (
    ask, ask_yes_no, ask_choice, dotify_if_no_dot,
    build_plans, check_conflicts_or_exit, preview_and_confirm, two_phase_rename,
    check_matches_and_retry,
    console, Colors
)
from rich.text import Text

def flow_movie_mode():
    console.print(f"\n[{Colors.MODE_TITLE_MAGENTA}]== 影视模式 ==[/]")
    
    # 1) 目录
    dir_str = ask("请输入目录路径", default=".")
    dir_path = Path(dir_str).expanduser().resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        console.print(f"[{Colors.ERROR}]目录不存在：[/]{dir_path}")
        sys.exit(1)

    # 2) 扩展名
    while True:
        ext_choice = ask_choice("请选择需要处理的扩展名：",
                                ["mkv", "mp4", "avi", "mov", "自定义"])
        if ext_choice == "自定义":
            ext = ask("请输入扩展名（不要带点）").strip().lstrip(".").lower()
        else:
            ext = ext_choice.strip().lstrip(".").lower()
        
        # 检查扩展名匹配的文件数量
        count, should_retry = check_matches_and_retry(dir_path, ext, match_src=None, flags="i")
        if not should_retry:
            break

    # 3) 匹配类型
    while True:
        console.print(f'\n[{Colors.SECONDARY}]匹配类型用于定位"集数标记"。[/]')
        match_choice = ask_choice("请选择匹配类型：",
                                [
                                "E(\\d+) - 匹配 E01, E02, e10 等格式（示例：Show.Name.E22.mkv；默认忽略大小写）",
                                "S\\d+\\.E(\\d+) - 匹配 S01.E01, S02.E05 等格式（示例：Show.Name.S01.E22.mkv；默认忽略大小写）",
                                "Ep(\\d+) - 匹配 Ep1, Ep10 等格式（示例：Show.Name.Ep22.mkv；默认忽略大小写）",
                                "自定义正则表达式 - 手动输入正则表达式，可自定义匹配选项"
                                ])

        if match_choice == "自定义正则表达式 - 手动输入正则表达式，可自定义匹配选项":
            # 自定义模式：需要用户输入正则表达式和匹配选项
            while True:
                match_src = ask("请输入自定义正则表达式（第一个捕获组必须是集数，例如：E(\\d+)，仅支持单个表达式）")
                # 检查是否包含逗号（多个表达式）
                if "," in match_src:
                    console.print(f"[{Colors.WARNING}]自定义模式仅支持单个正则表达式，不支持多个表达式（不能包含逗号）。[/]")
                    continue
                if match_src.strip() == "":
                    console.print(f"[{Colors.WARNING}]请输入有效的正则表达式。[/]")
                    continue
                
                # 验证正则表达式是否有捕获组
                try:
                    test_pattern = re.compile(match_src)
                    if test_pattern.groups == 0:
                        console.print(f"[{Colors.ERROR}]错误：正则表达式必须包含至少一个捕获组（用括号括起来），用于匹配集数。[/]")
                        # 使用 Text 对象来避免数字和特殊字符被意外着色
                        console.print(Text("示例：E(\\d+) 中的 (\\d+) 是捕获组", style=Colors.SECONDARY))
                        continue
                except re.error as e:
                    console.print(f"[{Colors.ERROR}]正则表达式格式错误：{e}[/]")
                    continue
                
                break
            
            # 询问匹配选项
            console.print(f"\n[{Colors.BOLD}]匹配选项说明：[/]")
            console.print(f"[{Colors.SECONDARY}]  i = 忽略大小写（推荐）[/]")
            console.print(f"[{Colors.SECONDARY}]  m = 多行模式[/]")
            console.print(f"[{Colors.SECONDARY}]  s = 点号匹配换行符[/]")
            console.print(f"[{Colors.SECONDARY}]  可组合使用，如：im, is, ims[/]")
            console.print(f"[{Colors.SECONDARY}]  直接回车 = 不使用任何匹配选项[/]")
            flags = ask("请输入匹配选项（直接回车表示不使用任何选项）", default="", allow_empty=True)
        else:
            # 预设模式：提取正则表达式部分
            if match_choice.startswith("E(\\d+)"):
                match_src = "E(\\d+)"
            elif match_choice.startswith("S\\d+\\.E(\\d+)"):
                match_src = "S\\d+\\.E(\\d+)"
            elif match_choice.startswith("Ep(\\d+)"):
                match_src = "Ep(\\d+)"
            else:
                match_src = match_choice.split(" - ")[0]  # 提取选项前的正则部分
            
            flags = "i"  # 默认忽略大小写
        
        # 检查匹配类型后的文件数量
        count, should_retry = check_matches_and_retry(dir_path, ext, match_src, flags, prompt_context="")
        if not should_retry:
            break

    # 4) 新前缀
    to_prefix = ask("请输入新的前缀（如：State.of.Divinity.S01）")
    to_prefix = dotify_if_no_dot(to_prefix)

    # 5) 后缀策略
    console.print(f'\n[{Colors.SECONDARY}]后缀 = 文件名中"集数标记"之后到扩展名前的全部内容。[/]')
    suf_mode = ask_choice("后缀处理方式：", ["保留原有后缀", "统一替换为我指定的后缀"])
    if suf_mode == "统一替换为我指定的后缀":
        suffix = ask("请输入后缀（不含扩展名）")
        suffix = dotify_if_no_dot(suffix)
    else:
        suffix = None  # 保留原尾巴

    # 6) 生成计划（使用默认值：不补零，因为集数格式保持原样）
    # 影视模式下，所有匹配类型都包含集数，集数格式保持原始文件的格式（不补零）
    start = 0  # 影视模式不使用起始编号
    sort_key = "name"  # 影视模式不使用排序（因为没有空匹配）
    padding_width = 0  # 不补零，保持原始集数格式
    
    plans = build_plans(dir_path, ext, match_src, flags, to_prefix, suffix, start, sort_key, padding_width)
    if not plans:
        console.print(f"[{Colors.WARNING}]未找到可重命名的文件（检查目录/扩展名/匹配条件）。[/]")
        sys.exit(0)

    # 7) 冲突检测 & 预览 & 执行
    # 影视模式不使用编号配置来解析冲突（使用默认值）
    plans = check_conflicts_or_exit(dir_path, plans, start, padding_width)
    if preview_and_confirm(dir_path, plans):
        two_phase_rename(dir_path, plans)
        console.print(f"[{Colors.SUCCESS_BOLD}]✅ 重命名完成。[/]")
    else:
        console.print(f"[{Colors.SECONDARY}]已取消。[/]")

