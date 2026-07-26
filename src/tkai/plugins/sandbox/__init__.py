"""Policy-based local execution sandbox for trusted plugin callables."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import TypeVar

from tkai.core.exceptions import PluginError

from ..permissions import PermissionPolicy

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ExecutionLimits:
    timeout_seconds: float = 30.0
    memory_bytes: int = 128 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0 or self.memory_bytes <= 0:
            raise ValueError("execution limits must be positive")


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    permissions: PermissionPolicy = PermissionPolicy()
    filesystem_roots: tuple[str, ...] = ()
    network_hosts: tuple[str, ...] = ()
    environment_keys: frozenset[str] = frozenset()
    limits: ExecutionLimits = ExecutionLimits()


class PluginSandbox:
    """Enforce permissions and bounded execution without mutating process globals."""

    def __init__(self, policy: SandboxPolicy) -> None:
        self.policy = policy

    def execute(self, function: Callable[..., T], *args: object, **kwargs: object) -> T:
        pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tkai-plugin")
        try:
            future = pool.submit(function, *args, **kwargs)
            try:
                return future.result(timeout=self.policy.limits.timeout_seconds)
            except FutureTimeout as exc:
                future.cancel()
                raise PluginError("Plugin execution timed out") from exc
        finally:
            pool.shutdown(wait=False, cancel_futures=True)


__all__ = ("ExecutionLimits", "PluginSandbox", "SandboxPolicy")
