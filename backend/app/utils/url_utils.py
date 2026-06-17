"""URL 工具函数 - 统一 API 端点拼接规范

核心设计目标：
1. 配置分离：基础域名版本、业务端点分开维护
2. 拼接无重复斜杠、无重复 /v1
3. 多模型/多服务兼容
4. 代码侧通用拼接工具，统一规则
5. 配置可序列化（JSON/YAML）

术语定义（强制统一命名）：
- base_url: 服务基础根地址，包含协议+域名+API版本/v1，结尾禁止带斜杠
- endpoint: 接口子路径，/v1之后的资源路径，开头禁止带斜杠
- full_url: 运行时动态拼接生成完整请求地址

拼接规则：full_url = trimEnd(base_url, "/") + "/" + trimStart(endpoint, "/")
"""
from typing import Optional


def trim_end_slash(value: str) -> str:
    """移除字符串末尾的斜杠"""
    return value.rstrip("/")


def trim_start_slash(value: str) -> str:
    """移除字符串开头的斜杠"""
    return value.lstrip("/")


def join_url(base_url: str, endpoint: str) -> str:
    """
    拼接 base_url 和 endpoint，自动消除两端多余斜杠
    
    Args:
        base_url: 服务基础根地址，如 "https://api.openai.com/v1"
        endpoint: 接口子路径，如 "chat/completions"
    
    Returns:
        完整的请求URL，如 "https://api.openai.com/v1/chat/completions"
    
    Examples:
        >>> join_url("https://api.openai.com/v1", "chat/completions")
        "https://api.openai.com/v1/chat/completions"
        
        >>> join_url("https://api.openai.com/v1/", "/chat/completions")
        "https://api.openai.com/v1/chat/completions"
        
        >>> join_url("https://api.example.com", "images/generations")
        "https://api.example.com/images/generations"
    """
    clean_base = trim_end_slash(base_url)
    clean_endpoint = trim_start_slash(endpoint)
    
    if not clean_base:
        return clean_endpoint
    if not clean_endpoint:
        return clean_base
    
    return f"{clean_base}/{clean_endpoint}"


def ensure_base_url_format(base_url: str) -> str:
    """
    确保 base_url 符合规范格式：结尾无斜杠
    
    Args:
        base_url: 原始 base_url
    
    Returns:
        规范化的 base_url
    """
    return trim_end_slash(base_url)


def ensure_endpoint_format(endpoint: str) -> str:
    """
    确保 endpoint 符合规范格式：开头无斜杠、全小写
    
    Args:
        endpoint: 原始 endpoint
    
    Returns:
        规范化的 endpoint
    """
    return trim_start_slash(endpoint).lower()


def validate_base_url(base_url: str) -> Optional[str]:
    """
    验证 base_url 格式是否正确
    
    Args:
        base_url: 待验证的 base_url
    
    Returns:
        错误信息，如果格式正确则返回 None
    """
    if not base_url:
        return "base_url 不能为空"
    
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        return "base_url 必须以 http:// 或 https:// 开头"
    
    if base_url.endswith("/"):
        return "base_url 结尾禁止带斜杠 /"
    
    return None


def validate_endpoint(endpoint: str) -> Optional[str]:
    """
    验证 endpoint 格式是否正确
    
    Args:
        endpoint: 待验证的 endpoint
    
    Returns:
        错误信息，如果格式正确则返回 None
    """
    if not endpoint:
        return "endpoint 不能为空"
    
    if endpoint.startswith("/"):
        return "endpoint 开头禁止带斜杠 /"
    
    if endpoint.endswith("/"):
        return "endpoint 结尾禁止带斜杠 /"
    
    if "//" in endpoint:
        return "endpoint 禁止包含连续斜杠 //"
    
    return None
