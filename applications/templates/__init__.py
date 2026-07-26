"""Built-in application templates."""

from applications.models import ApplicationTemplate

TEMPLATE_NAMES = (
    "Assistant",
    "Customer Service",
    "Sales",
    "HR",
    "Finance",
    "Legal",
    "Operations",
    "Developer",
    "Research",
)


class TemplateCatalog:
    def __init__(self) -> None:
        self._items = tuple(
            ApplicationTemplate(
                name.lower().replace(" ", "-"),
                name,
                name,
                f"Enterprise-ready {name.lower()} AI application.",
                {"sharing": "private", "status": "draft"},
            )
            for name in TEMPLATE_NAMES
        )

    def list(self) -> tuple[ApplicationTemplate, ...]:
        return self._items

    def get(self, template_id: str) -> ApplicationTemplate:
        try:
            return next(item for item in self._items if item.id == template_id)
        except StopIteration as error:
            raise KeyError(template_id) from error
