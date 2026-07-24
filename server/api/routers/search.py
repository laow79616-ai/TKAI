"""Read-only unified Search route adapter."""

from __future__ import annotations

from collections.abc import Callable

from server.search import SearchFilter, SearchQuery, SearchTarget

from ..dependencies import ApiDependencies
from ..models import SearchParameters, list_response, validate_search_parameters


def endpoint(
    dependencies: ApiDependencies,
) -> Callable[..., dict[str, object]]:
    """Bind validated query parameters to the injected Search service."""

    def search(
        keyword: str = "",
        target: str | None = None,
        publisher: str | None = None,
        package: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        version: str | None = None,
        status: str | None = None,
    ) -> dict[str, object]:
        parameters = validate_search_parameters(
            {
                "keyword": keyword,
                "target": target,
                "publisher": publisher,
                "package": package,
                "category": category,
                "tag": tag,
                "version": version,
                "status": status,
            }
        )
        result = dependencies.search_service.search(_query(parameters))
        return list_response(result.entries, total=result.total)

    return search


def _query(parameters: SearchParameters) -> SearchQuery:
    target = SearchTarget(parameters.target) if parameters.target is not None else None
    return SearchQuery(
        keyword=parameters.keyword,
        search_filter=SearchFilter(
            target=target,
            publisher=parameters.publisher,
            package=parameters.package,
            category=parameters.category,
            tag=parameters.tag,
            version=parameters.version,
            status=parameters.status,
        ),
    )
