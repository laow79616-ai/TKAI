"""Endpoint-independent proxy verification."""

from __future__ import annotations

import socket
import ssl
import time
from typing import Protocol

from ..models import Proxy, ProxyProtocol, VerificationResult


class VerificationTransport(Protocol):
    def resolve(self, host: str) -> bool: ...
    def tcp(self, host: str, port: int, timeout: float) -> bool: ...
    def tls(self, host: str, port: int, timeout: float) -> bool: ...
    def public_ip(self, proxy: Proxy, timeout: float) -> tuple[bool, str]: ...
    def geo(self, public_ip: str, country: str, region: str) -> bool: ...
    def authenticate(self, proxy: Proxy) -> bool: ...


class LocalVerificationTransport:
    """Bounded checks; public-IP and geo checks require injected adapters."""

    def resolve(self, host: str) -> bool:
        try:
            return bool(socket.getaddrinfo(host, None))
        except OSError:
            return False

    def tcp(self, host: str, port: int, timeout: float) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def tls(self, host: str, port: int, timeout: float) -> bool:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=timeout) as raw:
                with context.wrap_socket(raw, server_hostname=host):
                    return True
        except (OSError, ssl.SSLError):
            return False

    def public_ip(self, proxy: Proxy, timeout: float) -> tuple[bool, str]:
        return False, ""

    def geo(self, public_ip: str, country: str, region: str) -> bool:
        return not country and not region

    def authenticate(self, proxy: Proxy) -> bool:
        return not proxy.credential_reference


class ProxyVerifier:
    def __init__(
        self,
        transport: VerificationTransport | None = None,
        *,
        timeout_seconds: float = 3,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 30:
            raise ValueError("Verification timeout must be within (0, 30].")
        self.transport = transport or LocalVerificationTransport()
        self.timeout_seconds = timeout_seconds

    def verify(self, proxy: Proxy) -> VerificationResult:
        started = time.monotonic()
        dns = self.transport.resolve(proxy.host)
        tcp = dns and self.transport.tcp(proxy.host, proxy.port, self.timeout_seconds)
        tls = (
            tcp
            and proxy.protocol is ProxyProtocol.HTTPS
            and self.transport.tls(proxy.host, proxy.port, self.timeout_seconds)
        )
        public_ok, public_ip = self.transport.public_ip(proxy, self.timeout_seconds)
        return VerificationResult(
            proxy_id=proxy.id,
            dns_resolution=dns,
            tcp_connectivity=tcp,
            tls_handshake=tls if proxy.protocol is ProxyProtocol.HTTPS else True,
            public_ip_check=public_ok,
            geo_check=self.transport.geo(public_ip, proxy.country, proxy.region),
            protocol_validation=tcp,
            authentication_validation=self.transport.authenticate(proxy),
            latency_seconds=max(time.monotonic() - started, 0),
            public_ip=public_ip,
        )
