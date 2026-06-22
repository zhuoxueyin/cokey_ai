"""画布/任务生成结果写入资源仓库。"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import asset_service as mod


def test_register_generated_assets_skips_existing_url():
    async def _run():
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value={"_id": "existing"})
        mock_svc = MagicMock()
        mock_svc.collection = mock_col
        mock_svc.create = AsyncMock()

        with patch.object(mod, "get_asset_service", return_value=mock_svc):
            count = await mod.register_generated_assets_from_result(
                {"type": "image", "images": [{"url": "https://cdn.example/a.png"}]},
                task_id="t1",
                category="image",
            )

        assert count == 0
        mock_svc.create.assert_not_called()

    asyncio.run(_run())


def test_register_generated_assets_creates_image():
    async def _run():
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)
        mock_svc = MagicMock()
        mock_svc.collection = mock_col
        mock_svc.create = AsyncMock(return_value={"id": "new"})

        with patch.object(mod, "get_asset_service", return_value=mock_svc):
            with patch.object(
                mod,
                "_file_path_from_cdn_url",
                return_value=("assets/images/x.png", ["https://cdn/x.png"]),
            ):
                count = await mod.register_generated_assets_from_result(
                    {
                        "type": "image",
                        "images": [{"url": "https://cdn.example/a.png", "cdn_url": "https://cdn/x.png"}],
                    },
                    task_id="t1",
                    category="image",
                )

        assert count == 1
        mock_svc.create.assert_awaited_once()
        kwargs = mock_svc.create.await_args.kwargs
        assert kwargs["source_type"] == "generated"
        assert kwargs["category"] == "image"

    asyncio.run(_run())


def test_register_generated_assets_video():
    async def _run():
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)
        mock_svc = MagicMock()
        mock_svc.collection = mock_col
        mock_svc.create = AsyncMock(return_value={"id": "new"})

        with patch.object(mod, "get_asset_service", return_value=mock_svc):
            count = await mod.register_generated_assets_from_result(
                {"type": "video", "videos": [{"url": "https://cdn.example/v.mp4"}]},
                task_id="t2",
                category="video",
            )

        assert count == 1
        assert mock_svc.create.await_args.kwargs["category"] == "video"

    asyncio.run(_run())
