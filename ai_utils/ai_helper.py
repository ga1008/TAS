# ai_utils/ai_helper.py
from typing import Dict, List
from fastapi import HTTPException
from openai import AsyncOpenAI
from volcenginesdkarkruntime import AsyncArk
# [修正] 使用正确的事件类名
from volcenginesdkarkruntime.types.responses import (
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseTextDeltaEvent,  # 原 ResponseOutputTextDeltaEvent 是错误的
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

    # 2. 并发控制
    async with concurrency_manager.access(p_id, p_name, p_limit):
        try:
            response_content = ""

            # === 火山引擎 (针对多模态文件增强版) ===
            if platform_type == "volcengine":
                async with AsyncArk(api_key=api_key, base_url=base_url if base_url else None) as client:

                    # 检查是否包含 file_ids 或多模态 content（content 是列表）
                    has_files = any("file_ids" in m and m["file_ids"] for m in messages)
                    # 新增：检测 content 是否为列表（多模态内容：图片、视频等）
                    has_multimodal_content = any(
                        isinstance(m.get("content"), list)
                        for m in messages
                    )

                    if has_files or has_multimodal_content:
                        # --- 分支 A: 使用 Responses API (支持 File ID / PDF / 多模态) ---

                        user_content_list = []

                        # 处理多模态 content（新格式）
                        if has_multimodal_content:
                            # 直接使用多模态 content（已经包含 text, image_url, video_url）
                            for msg in messages:
                                if isinstance(msg.get("content"), list):
                                    user_content_list.extend(msg["content"])

                        # 处理 file_ids（旧格式兼容）
                        if has_files:
                            current_file_ids = []
                            current_text = ""

                            # 简单的合并逻辑：把所有 context 里的文件和文本都放到当前输入
                            for msg in messages:
                                if "file_ids" in msg:
                                    current_file_ids.extend(msg["file_ids"])
                                if msg["content"] and not isinstance(msg["content"], list):
                                    current_text += f"{msg['content']}\n"

                            # 1. 文件部分 (视频/PDF使用 video_url)
                            for fid in current_file_ids:
                                real_fid = fid.get("id") if isinstance(fid, dict) else fid
                                user_content_list.append({
                                    "type": "video_url",
                                    "video_url": {
                                        "url": real_fid
                                    }
                                })

                            # 2. 文本部分 (使用 text 而不是 input_text)
                            if current_text:
                                full_text = f"{system_prompt}\n\n{current_text}"
                                user_content_list.append({
                                    "type": "text",
                                    "text": full_text
                                })
                        else:
                            # 多模态模式下，添加 system_prompt 到第一个 text 元素
                            for i, item in enumerate(user_content_list):
                                if item.get("type") == "text":
                                    user_content_list[i] = {
                                        "type": "text",
                                        "text": f"{system_prompt}\n\n{item['text']}"
                                    }
                                    break
                            else:
                                # 如果没有 text 元素，添加一个
                                user_content_list.insert(0, {
                                    "type": "text",
                                    "text": system_prompt
                                })

                        # 调用 Responses Stream API
                        stream = await client.responses.create(
                            model=model_name,
                            input=[
                                {
                                    "role": "user",
                                    "content": user_content_list
                                }
                            ],
                            stream=True
                        )

                        # 处理流式响应
                        async for event in stream:
                            # [修正] 使用 ResponseTextDeltaEvent
                            if isinstance(event, ResponseTextDeltaEvent):
                                response_content += event.delta
                            # 也可以收集思考过程(Reasoning)，如果需要的话
                            if isinstance(event, ResponseReasoningSummaryTextDeltaEvent):
                                pass

                    else:
                        # --- 分支 B: 无文件，走标准 OpenAI 兼容接口 ---
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