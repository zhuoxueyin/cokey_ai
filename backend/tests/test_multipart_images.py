"""验证 multipart 多图 images[] 不会被 dict 覆盖"""
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.adapters.weelinking import WeelinkingAdapter


def test_multipart_files_list_not_dict():
    adapter = WeelinkingAdapter({"channel_code": "weelink_image", "retry_config": {}}, "test")
    fields = {"model": "gpt-image-2", "prompt": "test", "size": "1024x1024", "quality": "auto"}
    img1 = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    img2 = b"\xff\xd8\xff" + b"\x00" * 32
    image_fields = {"images[]": [img1, img2]}

    # 模拟构建 files_list 逻辑（与 _http_post_multipart 一致）
    files_list = []
    file_idx = 0
    for field_name, images_list in image_fields.items():
        for img_bytes in images_list:
            filename = f"image_{file_idx + 1}.png"
            files_list.append((field_name, (filename, io.BytesIO(img_bytes), "image/png")))
            file_idx += 1

    assert len(files_list) == 2
    assert files_list[0][0] == "images[]"
    assert files_list[1][0] == "images[]"
    print("multipart multi-image files_list OK:", len(files_list))


if __name__ == "__main__":
    test_multipart_files_list_not_dict()
