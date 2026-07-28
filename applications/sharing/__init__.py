"""Application sharing policy."""

from applications.models import Application, SharingScope


def can_view(
    application: Application,
    *,
    principal: str,
    teams: tuple[str, ...] = (),
    organization: str | None = None,
) -> bool:
    if principal == application.owner or application.sharing is SharingScope.PUBLIC:
        return True
    if application.sharing is SharingScope.TEAM:
        return bool(set(teams) & set(application.metadata.get("teams", ())))
    if application.sharing is SharingScope.ORGANIZATION:
        return organization is not None and organization == application.metadata.get(
            "organization"
        )
    return False
