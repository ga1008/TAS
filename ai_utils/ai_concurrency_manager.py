import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any


class ProviderConcurrencyManager:
    """
    (V4.5) AI 厂商并发控制器
    维护每个厂商(Provider ID)独立的信号量。
    支持运行时动态调整并发数（根据数据库配置自动扩缩容）。
    """

    def __init__(self):
        # 存储结构: { provider_id: {"sem": asyncio.Semaphore, "limit": int} }
        self._locks: Dict[int, Dict[str, Any]] = {}
        self._access_lock = asyncio.Lock()  # 保护 _locks 字典的线程安全

    @asynccontextmanager
    async def access(self, provider_id: int, provider_name: str, current_db_limit: int):
        """
        上下文管理器：获取特定厂商的并发锁。
        如果数据库中的 limit 变大了，会自动增加信号量容量。
        """
        target_sem = None

        # 1. 获取或创建信号量 (需要加锁防止竞态)
        async with self._access_lock:
            if provider_id not in self._locks:
                print(f"[Concurrency] 初始化厂商 [{provider_name}] (ID:{provider_id}) 并发锁: {current_db_limit}")
                self._locks[provider_id] = {
                    "sem": asyncio.Semaphore(current_db_limit),
                    "limit": current_db_limit
                }

            entry = self._locks[provider_id]
            target_sem = entry["sem"]
            old_limit = entry["limit"]

            # 2. 动态调整逻辑 (热更新)
            # 如果数据库里的配置变了 (例如从 3 变成 10)
            if current_db_limit != old_limit:
                diff = current_db_limit - old_limit
                if diff > 0:
                    # 扩容: 释放 diff 个令牌，允许更多并发
                    print(f"[Concurrency] [{provider_name}] 并发扩容: {old_limit} -> {current_db_limit}")
                    for _ in range(diff):
                        target_sem.release()
                elif diff < 0:
                    # 缩容: 仅更新记录，不强制 acquire (防止死锁)，
                    # 实际并发数会随着任务完成逐渐降低到新 limit
                    print(
                        f"[Concurrency] [{provider_name}] 并发缩容: {old_limit} -> {current_db_limit} (将在任务释放后生效)")

                # 更新记录的 limit
                entry["limit"] = current_db_limit

        # 3. 真正的并发控制 (Wait if full)
        # print(f"[DEBUG] [{provider_name}] 正在等待锁... (当前剩余: {target_sem._value})")
        async with target_sem:
            # print(f"[DEBUG] [{provider_name}]以此获得锁，开始执行...")
            yield


concurrency_manager = ProviderConcurrencyManager()
