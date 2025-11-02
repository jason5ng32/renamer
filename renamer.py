#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式批量重命名工具
主入口文件
"""
import sys
from utils import console, ask_choice, Colors
from i18n import t, set_language, load_languages, get_nested_value

def show_intro():
    """显示程序介绍（使用英文作为默认）"""
    # 在语言选择之前，使用英文显示介绍
    languages = load_languages()
    en_data = languages.get("en", {})
    
    console.print()
    title = get_nested_value(en_data, "main.title") or "🛠 Batch Rename Tool"
    console.print(f"[{Colors.TITLE}]{title}[/]")
    console.print()
    
    # 显示介绍文本
    intro_lines = get_nested_value(en_data, "main.intro")
    if isinstance(intro_lines, list):
        for line in intro_lines:
            if line:
                console.print(f"[{Colors.INFO}]{line}[/]")
            else:
                console.print()  # 空行
    elif intro_lines:
        console.print(f"[{Colors.INFO}]{intro_lines}[/]")
    console.print()

def select_language():
    """选择语言"""
    # 在语言选择时，先加载英文来显示语言选择提示
    # 因为此时还没有选择语言，所以使用英文作为默认显示
    languages = load_languages()
    en_data = languages.get("en", {})
    
    # 获取语言选择提示（使用英文）
    prompt_key = "main.language_prompt"
    prompt = get_nested_value(en_data, prompt_key) or "Select Language / 选择语言"
    
    # 语言选项（固定，不依赖翻译）
    language_options = {
        "English": "en",
        "中文 (Chinese)": "zh"
    }
    
    # 显示选项
    options = list(language_options.keys())
    choice = ask_choice(prompt, options)
    
    # 设置语言
    lang_code = language_options[choice]
    set_language(lang_code)
    return lang_code

def main():
    """主入口函数"""
    try:
        # 显示介绍
        show_intro()
        
        # 选择语言
        select_language()
        
        # 导入模式函数（在语言选择之后）
        from video_mode import flow_movie_mode
        from normal_mode import flow_normal_mode
        
        # 显示模式选择（使用翻译）
        mode_options = [t('main.mode_options.movie'), t('main.mode_options.regex')]
        mode_choice = ask_choice(t('main.mode_prompt'), mode_options)
        
        if mode_choice == t('main.mode_options.movie'):
            flow_movie_mode()
        else:
            flow_normal_mode()
    except KeyboardInterrupt:
        console.print(f"\n[{Colors.SECONDARY}]{t('main.cancelled')}[/]")
        sys.exit(0)
    except EOFError:
        # 处理某些环境下的 Ctrl+D
        console.print(f"\n[{Colors.SECONDARY}]{t('main.cancelled')}[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
