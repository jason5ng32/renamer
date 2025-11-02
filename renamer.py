#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式批量重命名工具
主入口文件
"""
import sys
from utils import console, ask_choice, Colors

def main():
    """主入口函数"""
    try:
        console.print(f"[{Colors.TITLE}]🛠 阿禅的批量重命名工具[/]")
        from video_mode import flow_movie_mode
        from normal_mode import flow_normal_mode
        
        mode_choice = ask_choice("请选择模式：", ["影视模式", "正则模式（完全自定义）"])
        if mode_choice == "影视模式":
            flow_movie_mode()
        else:
            flow_normal_mode()
    except KeyboardInterrupt:
        console.print(f"\n[{Colors.SECONDARY}]已取消操作。[/]")
        sys.exit(0)
    except EOFError:
        # 处理某些环境下的 Ctrl+D
        console.print(f"\n[{Colors.SECONDARY}]已取消操作。[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
