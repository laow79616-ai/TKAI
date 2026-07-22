"""Read-only AI diagnostics example without network access."""

from __future__ import annotations

from tkai.ai import DoctorService, ProviderManager


def run() -> dict[str, object]:
    """Return a JSON-ready doctor report for an empty local manager."""
    return DoctorService(ProviderManager()).run().to_dict()


if __name__ == "__main__":
    print(run())
