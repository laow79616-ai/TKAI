from typing import Protocol


class PlatformGateway(Protocol):
    def capabilities(self) -> tuple[object, ...]: ...
    def version(self) -> object: ...
    def health(self) -> object: ...


class CloudGateway(PlatformGateway, Protocol):
    pass


class WorkspaceGateway(PlatformGateway, Protocol):
    pass


class ProjectGateway(PlatformGateway, Protocol):
    pass


class DeploymentGateway(PlatformGateway, Protocol):
    pass


class ExecutionGateway(PlatformGateway, Protocol):
    pass


class StorageGateway(PlatformGateway, Protocol):
    pass
