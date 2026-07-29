"""Public Security Framework interfaces."""

from typing import Protocol

from ..contracts import AuthorizationDecision, AuthorizationRequest


class AuthorizationEvaluator(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision: ...


__all__ = ("AuthorizationEvaluator",)
