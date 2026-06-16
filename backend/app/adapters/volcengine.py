from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime
import time
import json
import asyncio

import httpx

from app.adapters.base import BaseChannelAdapter
from app.core.logging_config import get_logger

logger = get_logger()


def _join_url(base_url: str, path: str) -> str:
    """将 base_url 与 path 拼接成完整 URL"""
    base = base_url.rstrip("/")
    rel = path.lstrip("/")
    return f"{base}/{rel}"


class VolcengineAdapter(BaseChannelAdapter):
    """火山引擎渠道适配器 - 用于视频模型（seedancer）

    API 格式参考:
    视频生成（异步）:
    POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
    GET  https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{id}
    
    Authorization: Bearer <api_key>
    Content-Type: application/json
    
    请求体:
    {
        "model": "<model_name>",
        "prompt": "...",
        "image_urls": ["..."],
        "video_urls": ["..."],
        "audio_urls": ["..."],
        "generate_audio": true,
        "ratio": "16:9",
        "duration": 11,
        "watermark": true
    }
    
    响应格式（任务创建）:
    {
        "task_id": "xxx",
        "status": "running"
    }
    
    响应格式（任务查询）:
    {
        "task_id": "xxx",
        "status": "succeeded",
        "content": {
            "video_url": "https://..."
        }
    }
    """

    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        super().__init__(channel_config, trace_id)
        self.timeout = self.retry_config.get("timeout", 120)  # 视频生成需要更长时间
        self.poll_interval = self.retry_config.get("poll_interval", 5)  # 轮询间隔（秒）
        self.max_poll_attempts = self.retry_config.get("max_poll_attempts", 240)  # 最大轮询次数（20分钟 = 240 * 5秒）
        self.max_poll_records = 50  # 最大轮询记录数（防止文档过大）
        self._cancel_flag = False  # 取消标志，用于手动停止轮询
        self._create_response = None  # 记录创建任务的响应
        self._poll_attempts = []  # 记录轮询详情
        self.api_config = channel_config.get("api_config", {
            "text_path": "/api/v3/responses",
            "image_path": "/api/v3/responses",
            "video_path": "/api/v3/contents/generations/tasks",
            "text_stream": False,  # 火山引擎不支持流式
        })

    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """将平台参数转换为火山引擎格式 - 严格按照 Seedancer API 格式"""
        # 火山引擎视频 API 需要 content 字段
        content: List[Dict[str, Any]] = []
        
        # 添加文本内容 - 严格格式 {"type": "text", "text": "..."}
        if params.get("prompt"):
            content.append({
                "type": "text",
                "text": params["prompt"]
            })
        
        # 添加参考图片 - 严格格式 {"type": "image_url", "image_url": {"url": "..."}}
        if params.get("images") and isinstance(params["images"], list):
            for img in params["images"]:
                url = img.get("url") if isinstance(img, dict) else img
                if url:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": url}
                    })
        
        # 添加参考视频
        if params.get("videos") and isinstance(params["videos"], list):
            for video in params["videos"]:
                url = video.get("url") if isinstance(video, dict) else video
                if url:
                    content.append({
                        "type": "video_url",
                        "video_url": {"url": url}
                    })
        
        # 添加参考音频
        if params.get("audios") and isinstance(params["audios"], list):
            for audio in params["audios"]:
                url = audio.get("url") if isinstance(audio, dict) else audio
                if url:
                    content.append({
                        "type": "audio_url",
                        "audio_url": {"url": url}
                    })
        
        # 构建最终请求体 - 严格按照 Seedancer API 格式
        result: Dict[str, Any] = {
            "content": content,
            "generate_audio": params.get("audio", True),  # 默认开启音频生成
            "ratio": params.get("ratio", "adaptive"),     # 默认自适应比例
            "duration": params.get("duration", 5),        # 默认5秒
            "watermark": params.get("watermark", False),
        }
        
        # 添加视频质量参数（如果提供）
        if params.get("video_quality"):
            result["video_quality"] = params["video_quality"]
        
        logger.info(f"[{self.trace_id}] convert_params - result_keys={list(result.keys())}")
        logger.info(f"[{self.trace_id}] content_length={len(content)}")
        logger.info(f"[{self.trace_id}] content={json.dumps(content, ensure_ascii=False)[:500]}")
        
        return result

    async def _http_post(self, url: str, body: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """统一 HTTP POST 请求，带重试和日志"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"[{self.trace_id}] ═════════ POST {url}")
        try:
            safe_body = {k: v for k, v in body.items() if k != "api_key"}
            logger.info(f"[{self.trace_id}] body={json.dumps(safe_body, ensure_ascii=False, indent=2)[:800]}")
        except Exception:
            pass

        last_error = None
        max_retries = self.retry_config.get("max_retries", 1)

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=body, headers=headers)

                logger.info(f"[{self.trace_id}] HTTP {response.status_code} 响应 (attempt {attempt+1})")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"[{self.trace_id}] 响应数据长度={len(str(data))}")
                        return data
                    except Exception:
                        text = response.text[:300]
                        raise Exception(f"响应非 JSON 格式: {text}")
                else:
                    try:
                        err_json = response.json()
                        err_msg = json.dumps(err_json, ensure_ascii=False, indent=2)
                    except Exception:
                        err_msg = response.text[:500]
                    logger.error(f"[{self.trace_id}] 渠道错误响应 HTTP {response.status_code}:\n{err_msg}")

                    if response.status_code == 401:
                        raise Exception(f"401 Unauthorized - API Key 无效或过期 (渠道响应: {err_msg})")
                    elif response.status_code == 429:
                        raise Exception(f"429 Too Many Requests - 超出频率限制或配额不足 (渠道响应: {err_msg})")
                    elif response.status_code >= 500:
                        raise Exception(f"{response.status_code} Server Error (渠道响应: {err_msg})")
                    else:
                        raise Exception(f"HTTP {response.status_code}: {err_msg}")
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.trace_id}] HTTP 请求失败 (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("HTTP 请求失败")

    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """调用火山引擎 API"""
        path_map = {
            "text": self.api_config.get("text_path", "/api/v3/responses"),
            "image": self.api_config.get("image_path", "/api/v3/responses"),
            "video": self.api_config.get("video_path", "/api/v3/contents/generations/tasks"),
        }
        
        path = path_map.get(category, "/api/v3/responses")
        url = _join_url(self.base_url, path)
        
        # 构建火山引擎格式的请求体
        body = {
            "model": channel_model_id,
            **channel_params,
        }
        
        logger.info(f"[{self.trace_id}] call_api - category={category}, base_url={self.base_url}, model={channel_model_id}")
        logger.info(f"[{self.trace_id}] channel_params_keys={list(channel_params.keys())}")
        
        # 视频生成使用异步任务模式
        if category == "video":
            return await self._call_video_async(url, body, api_key)
        
        # 文本和图片使用同步模式
        return await self._http_post(url, body, api_key)
    
    async def _call_video_async(self, url: str, body: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """视频生成异步调用：创建任务 + 轮询状态"""
        logger.info(f"[{self.trace_id}] 开始视频异步生成流程")
        
        # 步骤1: 创建任务
        logger.info(f"[{self.trace_id}] 步骤1 - 创建视频生成任务")
        create_response = await self._http_post(url, body, api_key)
        
        # 火山引擎 API 返回的是 "id" 字段，不是 "task_id"
        task_id = create_response.get("id") or create_response.get("task_id")
        if not task_id:
            raise Exception(f"创建任务失败：未返回任务ID")
        
        logger.info(f"[{self.trace_id}] 任务创建成功，task_id={task_id}")
        
        # 步骤2: 轮询任务状态
        logger.info(f"[{self.trace_id}] 步骤2 - 开始轮询任务状态")
        status_url = f"{url}/{task_id}"
        
        # 记录创建响应（用于任务管理展示）
        self._create_response = create_response
        
        for attempt in range(self.max_poll_attempts):
            # 检查是否被取消
            if self._cancel_flag:
                logger.info(f"[{self.trace_id}] 轮询被手动停止")
                raise Exception("视频生成任务被用户手动停止")
            
            poll_start = time.time()
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }
                    response = await client.get(status_url, headers=headers)
                    
                    if response.status_code == 200:
                        task_result = response.json()
                        status = task_result.get("status")
                        duration_ms = int((time.time() - poll_start) * 1000)
                        
                        # 记录轮询详情（限制数量，防止文档过大）
                        self._poll_attempts.append({
                            "attempt": attempt + 1,
                            "status": status,
                            "http_status": response.status_code,
                            "duration_ms": duration_ms,
                            "timestamp": datetime.now().isoformat(),
                            "progress": task_result.get("progress")  # 如果 API 返回进度信息
                        })
                        # 保持轮询记录在限制范围内
                        if len(self._poll_attempts) > self.max_poll_records:
                            # 保留首尾各一半，丢弃中间部分
                            half = self.max_poll_records // 2
                            self._poll_attempts = self._poll_attempts[:half] + self._poll_attempts[-half:]
                        
                        logger.info(f"[{self.trace_id}] 轮询第 {attempt+1} 次 - 状态: {status}, 耗时: {duration_ms}ms")
                        
                        if status == "succeeded":
                            logger.info(f"[{self.trace_id}] 任务完成！")
                            return task_result
                        elif status == "failed":
                            error_msg = task_result.get("error", {}).get("message", "任务失败")
                            raise Exception(f"视频生成任务失败: {error_msg}")
                        elif status == "running" or status == "queued":
                            # 继续轮询
                            await asyncio.sleep(self.poll_interval)
                        else:
                            # 其他未知状态，继续轮询
                            await asyncio.sleep(self.poll_interval)
                    else:
                        duration_ms = int((time.time() - poll_start) * 1000)
                        self._poll_attempts.append({
                            "attempt": attempt + 1,
                            "status": "poll_error",
                            "http_status": response.status_code,
                            "duration_ms": duration_ms,
                            "timestamp": datetime.now().isoformat()
                        })
                        # 保持轮询记录在限制范围内
                        if len(self._poll_attempts) > self.max_poll_records:
                            half = self.max_poll_records // 2
                            self._poll_attempts = self._poll_attempts[:half] + self._poll_attempts[-half:]
                        logger.warning(f"[{self.trace_id}] 轮询失败 HTTP {response.status_code}")
                        await asyncio.sleep(self.poll_interval)
            except Exception as e:
                duration_ms = int((time.time() - poll_start) * 1000)
                self._poll_attempts.append({
                    "attempt": attempt + 1,
                    "status": "exception",
                    "http_status": None,
                    "duration_ms": duration_ms,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)[:200]  # 限制错误消息长度
                })
                # 保持轮询记录在限制范围内
                if len(self._poll_attempts) > self.max_poll_records:
                    half = self.max_poll_records // 2
                    self._poll_attempts = self._poll_attempts[:half] + self._poll_attempts[-half:]
                logger.warning(f"[{self.trace_id}] 轮询异常: {e}")
                await asyncio.sleep(self.poll_interval)
        
        raise Exception(f"视频生成任务超时（超过 {self.max_poll_attempts * self.poll_interval} 秒，约{int(self.max_poll_attempts * self.poll_interval / 60)}分钟）")
    
    def cancel(self):
        """取消轮询任务"""
        logger.info(f"[{self.trace_id}] 设置取消标志")
        self._cancel_flag = True

    async def parse_result(self, category: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """将火山引擎响应转换为平台统一格式"""
        result: Dict[str, Any] = {}
        
        # 视频生成结果（异步任务完成后的响应格式）
        if category == "video":
            # 异步任务完成后的响应格式: {"task_id": "...", "status": "succeeded", "content": {"video_url": "..."}}
            content = raw_result.get("content", {})
            video_url = content.get("video_url") or raw_result.get("video_url")
            
            if video_url:
                result["videos"] = [{
                    "url": video_url,
                    "width": raw_result.get("width"),
                    "height": raw_result.get("height"),
                    "duration": raw_result.get("duration")
                }]
            return result
        
        # 提取响应数据（文本和图片的同步响应格式）
        outputs = raw_result.get("output", {}).get("choices", [])
        if outputs:
            output = outputs[0]
            
            # 文本响应
            if category == "text":
                text = output.get("text") or output.get("content")
                if text:
                    result["text"] = text
            
            # 图片响应
            elif category == "image":
                image_url = output.get("image_url") or output.get("url")
                if image_url:
                    result["images"] = [{
                        "url": image_url,
                        "width": output.get("width"),
                        "height": output.get("height")
                    }]
        
        # 如果没有找到结构化结果，尝试从其他字段提取
        if not result:
            if raw_result.get("result"):
                result["text"] = str(raw_result["result"])
        
        logger.info(f"[{self.trace_id}] parse_result - category={category}, result_keys={list(result.keys())}")
        return result

    def parse_error(self, exception: Exception) -> tuple[str, str]:
        """将异常转换为统一错误码和消息"""
        msg = str(exception)
        if "401" in msg or "Unauthorized" in msg:
            return "auth_error", "API Key 无效或过期"
        elif "429" in msg or "Too Many Requests" in msg:
            return "rate_limit", "请求过于频繁，请稍后重试"
        elif "500" in msg or "Server Error" in msg:
            return "server_error", "服务端错误，请稍后重试"
        else:
            return "channel_error", msg[:200]

    async def query_task(self, external_task_id: str) -> Dict[str, Any]:
        """查询火山引擎视频任务状态（用于服务器重启后恢复任务）"""
        api_key = self.get_api_key_for_category("video")
        if not api_key:
            return {"success": False, "error_code": "auth_error", "error_message": "API Key 未配置"}
        
        path = self.api_config.get("video_path", "/api/v3/contents/generations/tasks")
        status_url = _join_url(self.base_url, f"{path}/{external_task_id}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        logger.info(f"[{self.trace_id}] 查询外部任务状态: {status_url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(status_url, headers=headers)
                
                if response.status_code == 200:
                    task_result = response.json()
                    status = task_result.get("status")
                    
                    if status == "succeeded":
                        # 任务已完成，解析结果
                        result = await self.parse_result("video", task_result)
                        return {"success": True, "data": result, "status": "completed"}
                    elif status == "failed":
                        error_msg = task_result.get("error", {}).get("message", "任务失败")
                        return {"success": False, "error_code": "task_failed", "error_message": error_msg, "status": "failed"}
                    elif status in ["running", "queued"]:
                        return {"success": False, "status": "running", "message": "任务仍在运行中"}
                    else:
                        return {"success": False, "status": "unknown", "message": f"未知状态: {status}"}
                else:
                    try:
                        err_json = response.json()
                        err_msg = err_json.get("message", f"HTTP {response.status_code}")
                    except Exception:
                        err_msg = response.text[:200]
                    return {"success": False, "error_code": "http_error", "error_message": err_msg}
        except Exception as e:
            logger.error(f"[{self.trace_id}] 查询外部任务失败: {e}")
            return {"success": False, "error_code": "query_failed", "error_message": str(e)}