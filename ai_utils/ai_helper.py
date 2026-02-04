# ai_utils/ai_helper.py
from typing import Dict, List
from fastapi import HTTPException
from openai import AsyncOpenAI
from volcenginesdkarkruntime import AsyncArk
from volcenginesdkarkruntime.types.responses import (
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseTextDeltaEvent,
    ResponseCompletedEvent
)
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

    # 2. 并发控制 (使用 with 而不是 async with)
    with concurrency_manager.access(p_id, p_name, p_limit):
        try:
            response_content = ""

            # === 火山引擎 (针对多模态文件增强版) ===
            if platform_type == "volcengine":
                async with AsyncArk(api_key=api_key, base_url=base_url if base_url else None) as client:

                    # 检查是否包含 file_ids 或多模态 content 列表
                    has_files = any("file_ids" in m and m["file_ids"] for m in messages)
                    has_multimodal_content = any(isinstance(m.get("content"), list) for m in messages)

                    if has_files or has_multimodal_content:
                        user_content_list = []

                        # A. 处理 System Prompt (作为第一个 input_text)
                        user_content_list.append({
                            "type": "input_text",
                            "text": f"{system_prompt}\n"
                        })

                        # B. 处理消息中的多模态内容
                        for msg in messages:
                            if msg["role"] == "user":
                                raw_content = msg["content"]

                                # 处理内容列表 (新标准)
                                if isinstance(raw_content, list):
                                    for item in raw_content:
                                        if item.get("type") in ["input_text", "input_file", "input_video",
                                                                "input_image"]:
                                            user_content_list.append(item)

                                # 处理纯文本 (兼顾旧版 file_ids 的情况)
                                elif isinstance(raw_content, str):
                                    # 先尝试查找该消息是否有 file_ids (旧版兼容逻辑)
                                    msg_file_ids = msg.get("file_ids", [])
                                    if msg_file_ids:
                                        # 如果有 file_ids，先添加文件
                                        # 注意：这里只能默认映射为 input_file，可能对图片不准确
                                        # 但这能保证文档解析功能恢复正常
                                        for fid in msg_file_ids:
                                            user_content_list.append({
                                                "type": "input_file",
                                                "file_id": fid
                                            })

                                    # 再添加文本
                                    user_content_list.append({
                                        "type": "input_text",
                                        "text": raw_content
                                    })

                        # 调用 Responses Stream API
                        stream = await client.responses.create(
                            model=model_name,
                            input=[{"role": "user", "content": user_content_list}],
                            stream=True
                        )

                        async for event in stream:
                            if isinstance(event, ResponseTextDeltaEvent):
                                response_content += event.delta
                            elif isinstance(event, ResponseReasoningSummaryTextDeltaEvent):
                                pass

                    else:
                        # --- 分支 B: 纯文本兼容模式 ---
                        final_messages = [{"role": "system", "content": system_prompt}, *n_messages]
                        extra_kwargs = {}
                        if "thinking" in model_name or "reasoner" in model_name:
                            extra_kwargs["thinking"] = {"type": "enabled"}

                        completion = await client.chat.completions.create(
                            model=model_name,
                            messages=final_messages,
                            timeout=600,
                            **extra_kwargs
                        )
                        response_content = completion.choices[0].message.content

            # === OpenAI 标准协议 ===
            elif platform_type == "openai":
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
            import traceback
            traceback.print_exc()
            raise HTTPException(500, f"Upstream API Error: {str(e)}")