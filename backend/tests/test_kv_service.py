"""KV 服务单元测试（MongoDB mock 可选；此处测逻辑层 key 结构）。"""
from app.services.kv_service import KVService


def test_key_doc():
    doc = KVService._key_doc("drama", "session:abc")
    assert doc == {"namespace": "drama", "key": "session:abc"}
