import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_utils.ai_helper import call_ai_platform_chat
# 引入数据库和并发管理器
from database import Database

load_dotenv()

AI_HOST = os.getenv("AI_HOST", "0.0.0.0")
AI_PORT = int(os.getenv("AI_PORT", 9011))

# 初始化数据库连接 (用于读取配置)
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[AI SERVER] 启动中... 监听 {AI_HOST}:{AI_PORT}")
    yield
    print("[AI SERVER] Shutting down...")
    db.close()


app = FastAPI(lifespan=lifespan)


# 请求模型只包含业务数据，不再包含 Key
class AIChatRequest(BaseModel):
    system_prompt: str
    messages: List[Dict[str, Any]]
    new_message: str
    model_capability: str = "standard"  # 指定能力：standard, thinking, vision


@app.post("/api/ai/chat")
async def ai_chat_task(req: AIChatRequest):
    """
    接收通用请求 -> 内部查库选择最佳模型 -> 内部并发控制 -> 调用 -> 返回
    """
    history = req.messages
    history.append({
        "role": "user",
        "content": req.new_message
    })

    try:
        # 1. 自主管理：查询数据库获取最佳配置
        # 注意：这里在 async 中调用了同步的 sqlite，对于低并发场景可接受。
        # 高并发建议使用 aiosqlite，但为保持代码一致性，此处直接调用。
        ai_config = db.get_best_ai_config(req.model_capability)
        # 降级策略：如果找不到 thinking，找 standard
        if not ai_config and req.model_capability == "thinking":
            print(f"[AI] 未找到 thinking 模型，降级为 standard")
            ai_config = db.get_best_ai_config("standard")

        if not ai_config:
            raise HTTPException(status_code=503, detail="暂无在运行的 AI 模型，请联系管理员在后台添加模型。")

        # 2. 执行调用 (传入查出来的配置)
        response_text = await call_ai_platform_chat(
            system_prompt=req.system_prompt,
            messages=history,
            platform_config=ai_config
        )

        return {"status": "success", "response_text": response_text}

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI 服务内部错误: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("ai_assistant:app", host=AI_HOST, port=AI_PORT)