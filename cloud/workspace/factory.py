"""Explicit factory for local Workspace descriptors without persistence."""

from __future__ import annotations

from collections.abc import Mapping

from ..models import CloudValue, Workspace


class WorkspaceFactory:
    """Construct workspace descriptors from explicit caller values only."""

    def create(
        self,
        workspace_id: str,
        account_id: str,
        name: str,
        *,
        region: str | None = None,
        metadata: Mapping[str, CloudValue] | None = None,
    ) -> Workspace:
        """Build a Workspace without inferring configuration or contacting a service."""
        return Workspace(
            workspace_id,
            account_id,
            name,
            region,
            {} if metadata is None else metadata,
        )
