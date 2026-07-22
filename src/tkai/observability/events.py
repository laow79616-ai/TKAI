"""Named typed runtime events."""

from .models import Event

RequestStarted = Event
RequestCompleted = Event
ProviderSelected = Event
ProviderFailed = Event
FallbackTriggered = Event
HealthChanged = Event
ConfigurationLoaded = Event
CredentialLoaded = Event
