import threading
from contextlib import contextmanager
from typing import Dict, Any

class ProviderConcurrencyManager:
    """
    (V5.0 - Thread Safe) AI 厂商并发控制器
    使用 threading 替代 asyncio，以支持多线程/多事件循环环境下的全局并发控制。
    """

    def __init__(self):
        # 存储结构: { provider_id: {"sem": threading.Semaphore, "limit": int} }
        self._locks: Dict[int, Dict[str, Any]] = {}
        self._access_lock = threading.Lock()  # 保护 _locks 字典的线程安全

    @contextmanager
    def access(self, provider_id: int, provider_name: str, current_db_limit: int):
        """
        上下文管理器：获取特定厂商的并发锁（阻塞式）。
        """
        target_sem = None

        # 1. 获取或创建信号量
        with self._access_lock:
            if provider_id not in self._locks:
                print(f"[Concurrency] 初始化厂商 [{provider_name}] (ID:{provider_id}) 并发锁: {current_db_limit}")
                self._locks[provider_id] = {
                    "sem": threading.Semaphore(current_db_limit),
                    "limit": current_db_limit
                }

            entry = self._locks[provider_id]
            target_sem = entry["sem"]
            old_limit = entry["limit"]

            # 2. 动态调整逻辑 (热更新)
            if current_db_limit != old_limit:
                diff = current_db_limit - old_limit
                if diff > 0:
                    # 扩容: 释放 diff 个令牌
                    print(f"[Concurrency] [{provider_name}] 并发扩容: {old_limit} -> {current_db_limit}")
                    for _ in range(diff):
                        target_sem.release()
                elif diff < 0:
                    # 缩容: 仅更新记录
                    print(f"[Concurrency] [{provider_name}] 并发缩容: {old_limit} -> {current_db_limit}")

                entry["limit"] = current_db_limit

        # 3. 真正的并发控制 (线程阻塞等待)
        # print(f"[DEBUG] [{provider_name}] Thread-{threading.get_ident()} 等待锁...")
        with target_sem:
            # print(f"[DEBUG] [{provider_name}] Thread-{threading.get_ident()}以此获得锁...")
            yield

concurrency_manager = ProviderConcurrencyManager()