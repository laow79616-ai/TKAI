from server.api.app import create_app
from tiktok.business_platform import GET_ROUTES, BusinessPlatform, openapi_contract
from tiktok.business_platform.models import BusinessScope, Health, MetadataRecord


def test_all_business_modules_and_safety_boundaries() -> None:
    platform = BusinessPlatform()
    modules = platform.modules()["data"]
    assert {item["id"] for item in modules} == {
        "accounts",
        "browsers",
        "proxies",
        "tasks",
        "content",
        "data",
        "ai-studio",
        "admin",
    }
    assert all(not item["execution_enabled"] for item in modules)
    assert platform.dashboard(BusinessScope())["compatibility"] == (
        "v6",
        "v7",
        "v8",
        "v9",
        "v10",
        "v11",
        "v12",
    )


def test_inventory_is_tenant_scoped_searchable_and_filterable() -> None:
    platform = BusinessPlatform()
    platform.add_metadata(
        MetadataRecord(
            "account-1",
            "Primary",
            "accounts",
            "inventory",
            health=Health.HEALTHY,
            tags=("priority",),
            group="growth",
        ),
        MetadataRecord("account-2", "Other", "accounts", "inventory", tenant="other"),
    )
    result = platform.inventory(
        BusinessScope(),
        module="accounts",
        query="primary",
        tag="priority",
        group="growth",
    )
    assert result["total"] == 1
    assert result["data"][0]["id"] == "account-1"
    assert platform.export_metadata(BusinessScope(), "accounts")["generated"] is False


def test_openapi_is_complete_get_only_and_integrated() -> None:
    contract = openapi_contract()
    assert set(contract["paths"]) == set(GET_ROUTES)
    assert all(set(operations) == {"get"} for operations in contract["paths"].values())
    schema = create_app().openapi()
    assert set(GET_ROUTES) <= set(schema["paths"])
    for path in GET_ROUTES:
        assert set(schema["paths"][path]) == {"get"}
