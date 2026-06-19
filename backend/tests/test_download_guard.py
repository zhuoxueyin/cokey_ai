"""远程下载 URL 校验"""

import pytest

from app.core.download_guard import validate_download_url


def test_validate_download_url_ok():
    assert validate_download_url("https://example.com/a.mp4") == "https://example.com/a.mp4"


def test_validate_download_url_rejects_private():
    with pytest.raises(ValueError, match="不允许"):
        validate_download_url("http://127.0.0.1/video.mp4")


def test_validate_download_url_rejects_file_scheme():
    with pytest.raises(ValueError, match="HTTP"):
        validate_download_url("file:///etc/passwd")
