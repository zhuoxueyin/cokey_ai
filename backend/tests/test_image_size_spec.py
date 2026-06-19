"""官方尺寸标准校验"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.image_size_spec import normalize_image_size, resolve_spec_id


def test_gpt_image_2_9_16_1k():
    params, err = normalize_image_size(
        {"size": "1024x1536"},
        model_code="gpt-image-2",
        channel_model_id="gpt-image-2",
    )
    assert err is None
    assert params["size"] == "1024x1536"
    assert params["aspect_ratio"] == "9:16"
    assert params["resolution"] == "1k"


def test_legacy_864_maps_invalid():
    _, err = normalize_image_size(
        {"size": "864x1536"},
        model_code="gpt-image-2",
        channel_model_id="gpt-image-2",
    )
    assert err is not None


def test_aspect_ratio_resolution_combo():
    params, err = normalize_image_size(
        {"aspect_ratio": "16:9", "resolution": "4k"},
        model_code="gpt-image-2",
        channel_model_id="gpt-image-2",
    )
    assert err is None
    assert params["size"] == "3840x2160"


def test_dall_e_3_limited():
    assert resolve_spec_id("dall-e-3", "dall-e-3") == "dall-e-3"
    params, err = normalize_image_size(
        {"size": "1024x1792"},
        model_code="dall-e-3",
        channel_model_id="dall-e-3",
    )
    assert err is None
    assert params["aspect_ratio"] == "9:16"

    _, err2 = normalize_image_size(
        {"size": "2048x2048"},
        model_code="dall-e-3",
        channel_model_id="dall-e-3",
    )
    assert err2 is not None


if __name__ == "__main__":
    test_gpt_image_2_9_16_1k()
    test_legacy_864_maps_invalid()
    test_aspect_ratio_resolution_combo()
    test_dall_e_3_limited()
    print("All image_size_spec tests passed")
