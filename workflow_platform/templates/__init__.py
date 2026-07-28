"""Searchable workflow template catalog."""

from dataclasses import replace

from workflow_platform.models import Scope, Workflow, WorkflowStatus


class TemplateCatalog:
    def __init__(self) -> None:
        self._items: dict[str, Workflow] = {}

    def add(self, workflow: Workflow) -> None:
        self._items[workflow.id] = workflow

    def search(
        self, query: str = "", category: str | None = None
    ) -> tuple[Workflow, ...]:
        lowered = query.lower()
        return tuple(
            item
            for item in self._items.values()
            if (
                not lowered
                or lowered in item.name.lower()
                or lowered in item.description.lower()
            )
            and (category is None or item.category == category)
        )

    def export(self, template_id: str) -> dict[str, object]:
        return self._items[template_id].to_dict()

    def import_template(self, payload: dict[str, object]) -> Workflow:
        from workflow_platform.service import workflow_from_payload

        item = workflow_from_payload(dict(payload))
        self.add(item)
        return item

    def clone(
        self, template_id: str, new_id: str, scope: Scope, owner: str
    ) -> Workflow:
        item = replace(
            self._items[template_id],
            id=new_id,
            tenant=scope.tenant,
            workspace=scope.workspace,
            owner=owner,
            status=WorkflowStatus.DRAFT,
            version=1,
        )
        return item
