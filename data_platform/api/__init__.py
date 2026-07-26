"""FastAPI-compatible Enterprise AI Data Platform routes."""

from typing import Any

from data_platform import DataPlatform, DataScope


def register_data_routes(app: Any, platform: DataPlatform) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["data"])

    def scope(tenant: str, workspace: str) -> DataScope:
        return DataScope(tenant, workspace)

    def listed(values: tuple[Any, ...]) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    add(
        "/data",
        lambda: {"status": "ready", "metrics": platform.metrics.snapshot()},
        ["GET"],
    )
    add(
        "/datasets",
        lambda tenant, workspace, query="": listed(
            platform.list_datasets(scope(tenant, workspace), query)
        ),
        ["GET"],
    )
    add(
        "/datasets",
        lambda payload: platform.create_dataset(dict(payload)).to_dict(),
        ["POST"],
    )
    add(
        "/pipelines",
        lambda tenant, workspace: listed(
            tuple(
                i
                for i in platform.pipelines.values()
                if i.tenant == tenant and i.workspace == workspace
            )
        ),
        ["GET"],
    )
    add(
        "/pipelines",
        lambda payload: platform.create_pipeline(dict(payload)).to_dict(),
        ["POST"],
    )
    add(
        "/lineage", lambda dataset_id: listed(platform.lineage_for(dataset_id)), ["GET"]
    )
    add(
        "/quality",
        lambda: {"data": [r.to_dict() for r in platform.quality_results.values()]},
        ["GET"],
    )
    add(
        "/classification",
        lambda tenant, workspace: {
            "data": [
                {"dataset_id": i.id, "classification": i.classification.value}
                for i in platform.list_datasets(scope(tenant, workspace))
            ]
        },
        ["GET"],
    )
