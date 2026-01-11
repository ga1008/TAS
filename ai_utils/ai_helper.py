# ai_utils/ai_helper.py
from typing import Dict, List
from fastapi import HTTPException
from openai import AsyncOpenAI
from volcenginesdkarkruntime import AsyncArk
from ai_utils.ai_concurrency_manager import concurrency_manager


def delete_thinking_content(text: str) -> str:
    """删除思考标签"""
    thinking_start = text.find("<thinking>")
    thinking_end = text.find("</thinking>")
    if thinking_start != -1 and thinking_end != -1 and thinking_end > thinking_start:
        clean_text = text[:thinking_start] + text[thinking_end + len("</thinking>"):]
        return clean_text.strip()
    return text.strip()


async def call_ai_platform_chat(
        system_prompt: str,
        messages: List[Dict],
        platform_config: Dict
) -> str:
    # 0. 清理历史消息中的思考内容
    n_messages = []
    for msg in messages:
        if msg["role"] == "assistant" and isinstance(msg["content"], str):
            msg["content"] = delete_thinking_content(msg["content"])
        n_messages.append(msg)

    # 1. 解析数据库字段
    try:
        p_id = platform_config["provider_id"]
        p_name = platform_config.get("provider_name", "Unknown")
        p_limit = platform_config.get("max_concurrent_requests", 3)

        platform_type = platform_config["provider_type"]
        model_name = platform_config["model_name"]
        api_key = platform_config["api_key"]
        base_url = platform_config.get("base_url", "")
    except KeyError as e:
        raise HTTPException(500, f"AI 配置解析错误，缺少字段: {e}")

    # 2. 并发控制
    async with concurrency_manager.access(p_id, p_name, p_limit):
        try:
            response_content = ""

            # === 火山引擎 (Base64 增强版 + 资源自动释放) ===
            if platform_type == "volcengine":
                # 【关键修复】使用 async with 确保 Client 在退出时自动关闭连接
                async with AsyncArk(api_key=api_key, base_url=base_url if base_url else None) as client:

                    # 构建符合 OpenAI Vision 协议的消息
                    final_messages_payload = [{"role": "system", "content": system_prompt}]

                    for msg in messages:
                        # 检查是否包含 file_ids/file_data (Direct AI Grader 发来的特殊结构)
                        if "file_ids" in msg and msg["file_ids"]:
                            content_list = []

                            # 1. 处理多媒体文件
                            for item in msg["file_ids"]:
                                # 兼容逻辑：如果是字典，取 type 和 data/id
                                if isinstance(item, dict):
                                    ftype = item.get("type", "image")
                                    # 如果有 data (Base64) 优先用 data，否则用 id (Video file-id)
                                    payload = item.get("data") or item.get("id")
                                else:
                                    # 旧逻辑兼容
                                    ftype = "image"
                                    payload = item

                                if ftype == "video":
                                    content_list.append({
                                        "type": "video_url",
                                        "video_url": {"url": payload}
                                    })
                                else:
                                    # 图片：使用 image_url，内容为 Base64 字符串
                                    content_list.append({
                                        "type": "image_url",
                                        "image_url": {"url": payload}
                                    })

                            # 2. 插入文本指令
                            content_list.append({
                                "type": "text",
                                "text": msg["content"]
                            })

                            final_messages_payload.append({
                                "role": msg["role"],
                                "content": content_list
                            })
                        else:
                            final_messages_payload.append(msg)

                    extra_kwargs = {}
                    if "thinking" in model_name or "reasoner" in model_name:
                        extra_kwargs["thinking"] = {"type": "enabled"}

                    completion = await client.chat.completions.create(
                        model=model_name,
                        messages=final_messages_payload,
                        timeout=600,
                        **extra_kwargs
                    )
                    response_content = completion.choices[0].message.content

            # === OpenAI 标准协议 (资源自动释放) ===
            elif platform_type == "openai":
                # 【关键修复】使用 async with
                async with AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=300.0) as client:
                    final_messages = [{"role": "system", "content": system_prompt}, *n_messages]
                    completion = await client.chat.completions.create(
                        model=model_name,
                        messages=final_messages
                    )
                    response_content = completion.choices[0].message.content

            else:
                raise HTTPException(400, f"不支持的协议类型: {platform_type}")

            return response_content or ""

        except Exception as e:
            print(f"[ERROR] {p_name} 调用失败: {e}")
            raise HTTPException(500, f"Upstream API Error: {str(e)}")