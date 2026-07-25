"""Named immutable runtime events with stable observability identifiers."""

from dataclasses import dataclass, field

from .models import Event


@dataclass(frozen=True, slots=True)
class RequestStarted(Event):
    """Emitted immediately before a provider request starts."""

    name: str = field(default="RequestStarted", init=False)


@dataclass(frozen=True, slots=True)
class RequestCompleted(Event):
    """Emitted after a provider request completes."""

    name: str = field(default="RequestCompleted", init=False)


@dataclass(frozen=True, slots=True)
class ProviderSelected(Event):
    """Emitted when routing selects a provider."""

    name: str = field(default="ProviderSelected", init=False)


@dataclass(frozen=True, slots=True)
class ProviderFailed(Event):
    """Emitted when a provider request fails."""

    name: str = field(default="ProviderFailed", init=False)


@dataclass(frozen=True, slots=True)
class FallbackTriggered(Event):
    """Emitted when fallback advances to another provider candidate."""

    name: str = field(default="FallbackTriggered", init=False)


@dataclass(frozen=True, slots=True)
class HealthChanged(Event):
    """Emitted when passive provider health changes status."""

    name: str = field(default="HealthChanged", init=False)


@dataclass(frozen=True, slots=True)
class ConfigurationLoaded(Event):
    """Emitted after local configuration has been resolved."""

    name: str = field(default="ConfigurationLoaded", init=False)


@dataclass(frozen=True, slots=True)
class CredentialLoaded(Event):
    """Emitted after a credential source is selected without exposing secrets."""

    name: str = field(default="CredentialLoaded", init=False)
