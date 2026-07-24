from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorageCapability:
    name: str
    enabled: bool = True
