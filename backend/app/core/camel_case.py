"""递归转换 dict 的 snake_case <-> camelCase"""
import re
from typing import Any


def to_camel_case(snake_str: str) -> str:
    """将 snake_case 字符串转换为 camelCase"""
    parts = snake_str.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def to_snake_case(camel_str: str) -> str:
    """将 camelCase 字符串转换为 snake_case"""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()


def convert_keys(data: Any) -> Any:
    """递归转换 dict/list 中所有 snake_case 键为 camelCase"""
    if isinstance(data, dict):
        return {to_camel_case(k): convert_keys(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys(item) for item in data]
    return data


def convert_keys_to_snake(data: Any) -> Any:
    """递归转换 dict/list 中所有 camelCase 键为 snake_case"""
    if isinstance(data, dict):
        return {to_snake_case(k): convert_keys_to_snake(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_snake(item) for item in data]
    return data