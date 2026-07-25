from cloud.gateway import (
    GatewayCapability,
    GatewayHealth,
    GatewayVersion,
    ReferencePlatformGateway,
)


def test_reference_gateway_is_offline_descriptor_adapter():
    gateway = ReferencePlatformGateway(
        (GatewayCapability("workspace"),),
        GatewayVersion("1.3.0"),
        GatewayHealth.HEALTHY,
    )
    assert gateway.capabilities()[0].name == "workspace"
    assert gateway.version().platform_version == "1.3.0"
    assert gateway.health() is GatewayHealth.HEALTHY
