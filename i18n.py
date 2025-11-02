#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际化模块
管理多语言支持
"""
import json
from pathlib import Path

# 默认语言（英文）
DEFAULT_LANGUAGE = "en"

# 当前语言
_current_language = DEFAULT_LANGUAGE

# 语言数据缓存
_languages = {}

def load_languages():
    """加载所有语言文件"""
    global _languages
    if _languages:
        return _languages
    
    # 语言文件目录
    lang_dir = Path(__file__).parent / "locales"
    if not lang_dir.exists():
        lang_dir.mkdir()
    
    # 加载所有语言文件
    _languages = {}
    for lang_file in lang_dir.glob("*.json"):
        lang_code = lang_file.stem
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                _languages[lang_code] = json.load(f)
        except Exception:
            # 如果文件损坏，跳过
            pass
    
    return _languages

def set_language(lang_code: str):
    """设置当前语言"""
    global _current_language
    _current_language = lang_code if lang_code in load_languages() else DEFAULT_LANGUAGE

def get_language() -> str:
    """获取当前语言代码"""
    return _current_language

def t(key: str, **kwargs):
    """
    翻译函数
    key: 翻译键（支持嵌套，使用点号分隔，如 "main.title"）
    kwargs: 格式化参数
    如果翻译不存在，返回英文翻译；如果英文也不存在，返回 key
    返回值可能是字符串或列表（如 intro 是列表）
    """
    languages = load_languages()
    
    # 先尝试当前语言
    lang_data = languages.get(_current_language, {})
    value = get_nested_value(lang_data, key)
    
    # 如果当前语言没有，尝试英文
    if value is None and _current_language != DEFAULT_LANGUAGE:
        en_data = languages.get(DEFAULT_LANGUAGE, {})
        value = get_nested_value(en_data, key)
    
    # 如果英文也没有，返回 key
    if value is None:
        return key
    
    # 如果值是字符串，尝试格式化
    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            # 如果格式化失败，返回原始值
            return value
    
    # 如果是列表或其他类型，直接返回
    return value

def get_nested_value(data: dict, key: str):
    """从嵌套字典中获取值"""
    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                return None
        else:
            return None
    return value

