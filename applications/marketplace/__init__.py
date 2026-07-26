"""Public application marketplace projection."""

from applications.catalog import ApplicationCatalog
from applications.models import Application, ApplicationStatus, SharingScope


class ApplicationMarketplace:
    def __init__(self, catalog: ApplicationCatalog) -> None:
        self.catalog = catalog

    def list(self) -> tuple[Application, ...]:
        return tuple(
            item
            for item in self.catalog.list()
            if item.status is ApplicationStatus.PUBLISHED
            and item.sharing is SharingScope.PUBLIC
        )
