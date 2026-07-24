from .models import GatewayHealth, GatewayVersion


class ReferencePlatformGateway:
    def __init__(self, capabilities=(), version=None, health=GatewayHealth.HEALTHY):
        self._capabilities = tuple(capabilities)
        self._version = version or GatewayVersion("1.3.0")
        self._health = health

    def capabilities(self):
        return self._capabilities

    def version(self):
        return self._version

    def health(self):
        return self._health
