# -*- coding: utf-8 -*-
"""验证 GitHub 存储配置是否正确加载"""
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings

print("=" * 60)
print("配置加载验证")
print("=" * 60)
print(f"APP_NAME:    {settings.app_name}")
print(f"GITHUB_REPO: {settings.github_repo}")
print(f"GITHUB_BRANCH: {settings.github_branch}")
print(f"GITHUB_CDN_PREFIX: {settings.github_cdn_prefix}")

token = settings.github_token or ""
if token:
    display = token[:12] + "..." if len(token) > 12 else token
    print(f"GITHUB_TOKEN: {display} (长度: {len(token)})")
else:
    print("GITHUB_TOKEN: (空)")

print()
print("=" * 60)
print("存储服务状态")
print("=" * 60)

from app.services.storage_service import get_storage_service
svc = get_storage_service()

print(f"已启用: {'YES' if svc.enabled else 'NO'}")
print(f"仓库:   {svc.repo}")
print(f"分支:   {svc.branch}")
print(f"CDN:    {svc.cdn_base}")

print()
if svc.enabled:
    print("[OK] 存储服务已就绪，可以上传图片")
    print()
    print("上传后图片 URL 示例:")
    print(f"  {svc.cdn_base}/{svc.repo}@{svc.branch}/assets/images/20260615/abc123.png")
else:
    print("[!] 存储服务未启用")
    print()
    print("解决方法:")
    print("  1. 访问 https://github.com/settings/tokens 生成 PAT (勾选 repo 权限)")
    print(f"  2. 编辑 {os.path.join(BACKEND_DIR, '.env')}")
    print("  3. 将 GITHUB_TOKEN=your-github-personal-access-token-here")
    print("     替换为: GITHUB_TOKEN=ghp_你的真实Token")
    print("  4. 重启后端服务: python launcher.py restart")
