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
from i18n import t

def flow_movie_mode():
    console.print(f"\n[{Colors.MODE_TITLE_MAGENTA}]{t('movie_mode.title')}[/]")
    
    # 1) 目录
    dir_str = ask(t('common.dir_prompt'), default=".")
    dir_path = Path(dir_str).expanduser().resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        console.print(f"[{Colors.ERROR}]{t('common.dir_not_exists')}[/]{dir_path}")
        sys.exit(1)

    # 2) 扩展名
    while True:
        ext_choice = ask_choice(t('movie_mode.ext_prompt'),
                                ["mkv", "mp4", "avi", "mov", t('movie_mode.ext_custom')])
        if ext_choice == t('movie_mode.ext_custom'):
            ext = ask(t('movie_mode.ext_custom_prompt')).strip().lstrip(".").lower()
        else:
            ext = ext_choice.strip().lstrip(".").lower()
        
        # 检查扩展名匹配的文件数量
        count, should_retry = check_matches_and_retry(dir_path, ext, match_src=None, flags="i")
        if not should_retry:
            break

    # 3) 匹配类型
    while True:
        console.print(f'\n[{Colors.SECONDARY}]{t("movie_mode.match_type_info")}[/]')
        match_choice = ask_choice(t('movie_mode.match_type_prompt'),
                                [
                                t('movie_mode.match_options.e_digit'),
                                t('movie_mode.match_options.s_e_digit'),
                                t('movie_mode.match_options.ep_digit'),
                                t('movie_mode.match_options.custom')
                                ])

        if match_choice == t('movie_mode.match_options.custom'):
            # 自定义模式：需要用户输入正则表达式和匹配选项
            while True:
                match_src = ask(t('movie_mode.custom_regex_prompt'))
                # 检查是否包含逗号（多个表达式）
                if "," in match_src:
                    console.print(f"[{Colors.WARNING}]{t('movie_mode.custom_regex_single_only')}[/]")
                    continue
                if match_src.strip() == "":
                    console.print(f"[{Colors.WARNING}]{t('movie_mode.custom_regex_valid')}[/]")
                    continue
                
                # 验证正则表达式是否有捕获组
                try:
                    test_pattern = re.compile(match_src)
                    if test_pattern.groups == 0:
                        console.print(f"[{Colors.ERROR}]{t('movie_mode.regex_need_capture')}[/]")
                        # 使用 Text 对象来避免数字和特殊字符被意外着色
                        console.print(Text(t('movie_mode.regex_capture_example'), style=Colors.SECONDARY))
                        continue
                except re.error as e:
                    console.print(f"[{Colors.ERROR}]{t('movie_mode.regex_format_error')}[/]{e}")
                    continue
                
                break
            
            # 询问匹配选项
            console.print(f"\n[{Colors.BOLD}]{t('movie_mode.match_options_info')}[/]")
            console.print(Text(t('movie_mode.match_options_i'), style=Colors.SECONDARY))
            console.print(Text(t('movie_mode.match_options_m'), style=Colors.SECONDARY))
            console.print(Text(t('movie_mode.match_options_s'), style=Colors.SECONDARY))
            console.print(Text(t('movie_mode.match_options_combine'), style=Colors.SECONDARY))
            console.print(Text(t('movie_mode.match_options_empty'), style=Colors.SECONDARY))
            flags = ask(t('movie_mode.match_options_prompt'), default="", allow_empty=True)
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
    to_prefix = ask(t('movie_mode.new_prefix_prompt'))
    to_prefix = dotify_if_no_dot(to_prefix)

    # 5) 后缀策略
    console.print(f'\n[{Colors.SECONDARY}]{t("movie_mode.suffix_info")}[/]')
    suf_mode = ask_choice(t('movie_mode.suffix_mode_prompt'), 
                         [t('movie_mode.suffix_mode_options.keep'), t('movie_mode.suffix_mode_options.replace')])
    if suf_mode == t('movie_mode.suffix_mode_options.replace'):
        suffix = ask(t('movie_mode.suffix_prompt'))
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
        console.print(f"[{Colors.WARNING}]{t('common.not_found_files')}[/]")
        sys.exit(0)

    # 7) 冲突检测 & 预览 & 执行
    # 影视模式不使用编号配置来解析冲突（使用默认值）
    plans = check_conflicts_or_exit(dir_path, plans, start, padding_width)
    if preview_and_confirm(dir_path, plans):
        two_phase_rename(dir_path, plans)
        console.print(f"[{Colors.SUCCESS_BOLD}]{t('common.rename_complete')}[/]")
    else:
        console.print(f"[{Colors.SECONDARY}]{t('common.cancelled_operation')}[/]")

